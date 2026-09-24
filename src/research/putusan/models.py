from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class LegalSectionType(str, Enum):
    KEPALA_PUTUSAN = "KEPALA_PUTUSAN"
    IDENTITAS_PIHAK = "IDENTITAS_PIHAK"
    DUDUK_PERKARA = "DUDUK_PERKARA"
    PERTIMBANGAN_HUKUM = "PERTIMBANGAN_HUKUM"
    AMAR_PUTUSAN = "AMAR_PUTUSAN"
    PENUTUP = "PENUTUP"
    LAINNYA = "LAINNYA"


@dataclass
class PutusanMetadata:
    nomor_putusan: str = "TIDAK_TERDETEKSI"
    pengadilan: str = "TIDAK_TERDETEKSI"
    tingkat_peradilan: str = "Lainnya"
    klasifikasi: str = "Lainnya"
    pihak_utama: str = ""
    pihak_detail: dict[str, list[str]] = field(default_factory=dict)
    tanggal_putusan: str | None = None
    majelis_hakim: list[str] = field(default_factory=list)
    panitera: str | None = None
    amar_ringkas: str | None = None
    total_halaman: int = 0
    raw_header: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PutusanSection:
    section_type: LegalSectionType
    title: str
    page_start: int
    page_end: int
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_type": self.section_type.value,
            "title": self.title,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "content": self.content,
        }


@dataclass
class PutusanChunk:
    chunk_id: str
    doc_id: str
    nomor_putusan: str
    pengadilan: str
    tingkat: str
    klasifikasi: str
    pihak: str
    section: str
    subsection: str | None
    page_start: int
    page_end: int
    chunk_index: int
    total_chunks: int
    content: str
    context_header: str
    full_text: str
    char_count: int
    token_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PutusanDocument:
    doc_id: str
    file_path: str
    metadata: PutusanMetadata
    normalized_markdown: str
    sections: list[PutusanSection] = field(default_factory=list)
    chunks: list[PutusanChunk] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "file_path": self.file_path,
            "metadata": self.metadata.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "chunks": [c.to_dict() for c in self.chunks],
            "chunk_count": len(self.chunks),
            "section_count": len(self.sections),
            "total_halaman": self.metadata.total_halaman,
        }
