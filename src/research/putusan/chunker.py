from __future__ import annotations

import re
from typing import TYPE_CHECKING

from research.putusan.models import PutusanChunk

if TYPE_CHECKING:
    from research.putusan.models import PutusanDocument, PutusanMetadata, PutusanSection


def _estimate_tokens(text: str) -> int:
    """Rough token count estimation (~4 characters per token for Indonesian legal text)."""
    return max(1, len(text) // 4)


def _split_into_paragraphs(text: str) -> list[str]:
    """Split legal text into coherent semantic paragraphs."""
    # Split on double newlines or lines starting with legal paragraph markers
    raw_paras = re.split(r"\n\s*\n+", text)
    paras: list[str] = []

    for p in raw_paras:
        p_clean = p.strip()
        if not p_clean:
            continue

        # If paragraph has embedded 'Menimbang' or 'Mengingat' on newline, split further
        sub_paras = re.split(
            r"(?<=\n)(?=(?:MENIMBANG|Menimbang|MENGINGAT|Mengingat|MEMPERHATIKAN|Memperhatikan|\d+\.\s+[A-Z]|\[\d+\.\d+\]))",
            p_clean,
        )
        for sp in sub_paras:
            sp_clean = sp.strip()
            if sp_clean:
                paras.append(sp_clean)

    return paras


def _split_long_paragraph(
    text: str, max_chars: int = 1500, overlap_chars: int = 150
) -> list[str]:
    """Split an oversized single legal paragraph into sentence-aware sub-chunks."""
    # Split by Indonesian legal sentence terminators
    sentences = re.split(r"(?<=[;\.\?!])\s+(?=[A-Z0-9\(\"“])", text)
    chunks: list[str] = []
    current_sentences: list[str] = []
    current_len = 0

    for s in sentences:
        s_len = len(s)
        if current_len + s_len > max_chars and current_sentences:
            chunk_str = " ".join(current_sentences)
            chunks.append(chunk_str)

            # Keep sentences for overlap
            overlap_sentences: list[str] = []
            overlap_len = 0
            for os_item in reversed(current_sentences):
                if overlap_len + len(os_item) <= overlap_chars:
                    overlap_sentences.insert(0, os_item)
                    overlap_len += len(os_item)
                else:
                    break
            current_sentences = overlap_sentences
            current_len = sum(len(x) for x in current_sentences)

        current_sentences.append(s)
        current_len += s_len

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks or [text]


def chunk_section(
    section: PutusanSection,
    doc_id: str,
    metadata: PutusanMetadata,
    max_chunk_chars: int = 1500,
    overlap_chars: int = 150,
) -> list[PutusanChunk]:
    """Chunk a single legal section while preserving context."""
    paragraphs = _split_into_paragraphs(section.content)
    raw_chunks: list[str] = []

    current_para_group: list[str] = []
    current_chars = 0

    for para in paragraphs:
        para_len = len(para)
        # If single paragraph exceeds max_chunk_chars, split it
        if para_len > max_chunk_chars:
            if current_para_group:
                raw_chunks.append("\n\n".join(current_para_group))
                current_para_group = []
                current_chars = 0
            sub_chunks = _split_long_paragraph(para, max_chunk_chars, overlap_chars)
            raw_chunks.extend(sub_chunks)
            continue

        if current_chars + para_len > max_chunk_chars and current_para_group:
            raw_chunks.append("\n\n".join(current_para_group))
            current_para_group = [para]
            current_chars = para_len
        else:
            current_para_group.append(para)
            current_chars += para_len + 2

    if current_para_group:
        raw_chunks.append("\n\n".join(current_para_group))

    # Calculate page distribution for chunks in this section
    total_sec_chunks = len(raw_chunks)
    page_span = max(1, section.page_end - section.page_start + 1)

    result_chunks: list[PutusanChunk] = []

    for idx, content in enumerate(raw_chunks):
        if not content.strip():
            continue

        # Approximate page interpolation
        if total_sec_chunks > 1:
            fraction_start = idx / total_sec_chunks
            fraction_end = (idx + 1) / total_sec_chunks
            chunk_p_start = section.page_start + int(fraction_start * page_span)
            chunk_p_end = section.page_start + int(fraction_end * page_span)
            chunk_p_start = min(chunk_p_start, section.page_end)
            chunk_p_end = min(max(chunk_p_start, chunk_p_end), section.page_end)
        else:
            chunk_p_start = section.page_start
            chunk_p_end = section.page_end

        # Derive subsection title from first words
        first_line = content.split("\n")[0].strip()
        first_line_clean = re.sub(r"^[0-9\.\-\–\s]+", "", first_line)
        subsection = first_line_clean[:60] if len(first_line_clean) > 5 else section.title

        # Build context header banner
        pihak_part = f" | {metadata.pihak_utama}" if metadata.pihak_utama else ""
        pages_part = (
            f"Hal. {chunk_p_start}"
            if chunk_p_start == chunk_p_end
            else f"Hal. {chunk_p_start}-{chunk_p_end}"
        )

        context_header = (
            f"[PUTUSAN: {metadata.nomor_putusan} | {metadata.pengadilan} | "
            f"Tingkat: {metadata.tingkat_peradilan}{pihak_part} | "
            f"Bagian: {section.section_type.value} > {subsection} | {pages_part}]"
        )

        full_text = f"{context_header}\n\n{content}"

        result_chunks.append(
            PutusanChunk(
                chunk_id=f"{doc_id}_c{idx:04d}",
                doc_id=doc_id,
                nomor_putusan=metadata.nomor_putusan,
                pengadilan=metadata.pengadilan,
                tingkat=metadata.tingkat_peradilan,
                klasifikasi=metadata.klasifikasi,
                pihak=metadata.pihak_utama,
                section=section.section_type.value,
                subsection=subsection,
                page_start=chunk_p_start,
                page_end=chunk_p_end,
                chunk_index=idx,
                total_chunks=total_sec_chunks,
                content=content,
                context_header=context_header,
                full_text=full_text,
                char_count=len(full_text),
                token_count=_estimate_tokens(full_text),
            )
        )

    return result_chunks


def chunk_putusan_document(
    doc: PutusanDocument,
    max_chunk_chars: int = 1500,
    overlap_chars: int = 150,
) -> list[PutusanChunk]:
    """Execute context-preserving semantic chunking across all sections of a PutusanDocument."""
    all_chunks: list[PutusanChunk] = []
    global_index = 0

    for section in doc.sections:
        sec_chunks = chunk_section(
            section=section,
            doc_id=doc.doc_id,
            metadata=doc.metadata,
            max_chunk_chars=max_chunk_chars,
            overlap_chars=overlap_chars,
        )
        for c in sec_chunks:
            c.chunk_id = f"{doc.doc_id}_c{global_index:04d}"
            c.chunk_index = global_index
            all_chunks.append(c)
            global_index += 1

    # Update total chunks
    total = len(all_chunks)
    for c in all_chunks:
        c.total_chunks = total

    return all_chunks
