from __future__ import annotations

import re
from pathlib import Path

from research.putusan.models import PutusanMetadata

COURT_HIERARCHY_PATTERNS = [
    (
        "Pengadilan Tindak Pidana Korupsi",
        re.compile(
            r"Pengadilan Tindak Pidana Korupsi pada Pengadilan Negeri\s+([A-Za-z\s]+?)(?:\s+Klas|\s+Kelas|\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Hubungan Industrial",
        re.compile(
            r"Pengadilan Hubungan Industrial pada Pengadilan Negeri\s+([A-Za-z\s]+?)(?:\s+Klas|\s+Kelas|\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Niaga",
        re.compile(
            r"Pengadilan Niaga pada Pengadilan Negeri\s+([A-Za-z\s]+?)(?:\s+Klas|\s+Kelas|\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Negeri",
        re.compile(
            r"Pengadilan Negeri\s+([A-Za-z\s]+?)(?:\s+Klas|\s+Kelas|\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Tinggi Tata Usaha Negara",
        re.compile(
            r"Pengadilan Tinggi Tata Usaha Negara\s+([A-Za-z\s]+?)(?:\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Tata Usaha Negara",
        re.compile(
            r"Pengadilan Tata Usaha Negara\s+([A-Za-z\s]+?)(?:\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Tinggi Agama",
        re.compile(
            r"Pengadilan Tinggi Agama\s+([A-Za-z\s]+?)(?:\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Agama",
        re.compile(
            r"Pengadilan Agama\s+([A-Za-z\s]+?)(?:\s+Klas|\s+Kelas|\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Militer",
        re.compile(
            r"Pengadilan Militer\s+([A-Za-z0-9\-\/\s]+?)(?:\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "Pengadilan Tinggi",
        re.compile(
            r"Pengadilan Tinggi\s+([A-Za-z\s]+?)(?:\s+yang|\r?\n|$)",
            re.IGNORECASE,
        ),
    ),
    ("Mahkamah Konstitusi", re.compile(r"MAHKAMAH KONSTITUSI(?:\s+REPUBLIK INDONESIA)?", re.IGNORECASE)),
    ("Mahkamah Agung", re.compile(r"MAHKAMAH AGUNG(?:\s+REPUBLIK INDONESIA)?", re.IGNORECASE)),
    ("Dewan Kehormatan Penyelenggara Pemilu", re.compile(r"DEWAN KEHORMATAN PENYELENGGARA PEMILIH(?:AN)? UMUM", re.IGNORECASE)),
    ("Majelis Kehormatan Mahkamah Konstitusi", re.compile(r"MAJELIS KEHORMATAN MAHKAMAH KONS(?:TI)?TUSI", re.IGNORECASE)),
    ("Komisi Informasi Pusat", re.compile(r"KOMISI INFORMASI PUSAT(?:\s+REPUBLIK INDONESIA)?", re.IGNORECASE)),
]


def extract_nomor_putusan(first_pages_text: str, file_path: str = "") -> str:
    """Extract case number from the document header with fallback to filename."""
    # Pattern 1: Explicit Nomor : ...
    patterns = [
        re.compile(r"(?:PUTUSAN|PENETAPAN)?\s*(?:Nomor|NOMOR)\s*[:\.]?\s*([0-9A-Za-z\.\/\-\_ ]+?)(?=\r?\n|DEMI|$)", re.IGNORECASE),
        re.compile(r"NOMOR\s+REGISTRASI\s*[:\.]?\s*([0-9A-Za-z\.\/\-\_ ]+?)(?=\r?\n|$)", re.IGNORECASE),
        re.compile(r"Perkara\s+Nomor\s*[:\.]?\s*([0-9A-Za-z\.\/\-\_ ]+?)(?=\r?\n|,|$)", re.IGNORECASE),
    ]

    for pat in patterns:
        m = pat.search(first_pages_text)
        if m:
            val = m.group(1).strip()
            # Clean trailing noise
            val = re.sub(r"[\.;,:]+$", "", val).strip()
            if len(val) >= 4 and any(c.isdigit() for c in val):
                return val

    # Fallback to filename parsing if header extraction failed or was generic
    if file_path:
        stem = Path(file_path).stem
        # e.g. PUTUSAN-MA-1466-K-PID-2024 -> 1466 K/Pid/2024
        # e.g. PUTUSAN-PN-JAKPUS-71-PID-SUS-TPK-2024-PN-JKT-PST -> 71/Pid.Sus-TPK/2024/PN Jkt.Pst
        stem_clean = stem.replace("PUTUSAN-", "").replace("SALINAN-", "")
        return stem_clean

    return "TIDAK_TERDETEKSI"


def extract_pengadilan(first_pages_text: str, file_path: str = "") -> tuple[str, str]:
    """Extract court name and court level (tingkat peradilan)."""
    court_name = "TIDAK_TERDETEKSI"
    tingkat = "Lainnya"

    for base_type, pat in COURT_HIERARCHY_PATTERNS:
        m = pat.search(first_pages_text)
        if m:
            if m.groups():
                loc = m.group(1).strip()
                loc = re.sub(r"\s+", " ", loc).title()
                court_name = f"{base_type} {loc}".strip()
            else:
                court_name = base_type
            break

    # If still not found, check path directory
    if court_name == "TIDAK_TERDETEKSI" and file_path:
        p_up = file_path.upper()
        if "PUTUSAN-MK" in p_up:
            court_name = "Mahkamah Konstitusi"
        elif "PUTUSAN-MA" in p_up:
            court_name = "Mahkamah Agung"
        elif "PUTUSAN-DKPP" in p_up:
            court_name = "Dewan Kehormatan Penyelenggara Pemilu"
        elif "PUTUSAN-MKMK" in p_up:
            court_name = "Majelis Kehormatan Mahkamah Konstitusi"
        elif "PUTUSAN-KIP" in p_up:
            court_name = "Komisi Informasi Pusat"
        elif "PUTUSAN-PA" in p_up:
            court_name = "Pengadilan Agama"
        elif "PUTUSAN-PN" in p_up:
            court_name = "Pengadilan Negeri"
        elif "PUTUSAN-PTUN" in p_up:
            court_name = "Pengadilan Tata Usaha Negara"
        elif "PUTUSAN-PT" in p_up:
            court_name = "Pengadilan Tinggi"
        elif "PUTUSAN-PM" in p_up:
            court_name = "Pengadilan Militer"

    # Infer tingkat peradilan
    c_up = court_name.upper()
    if "MAHKAMAH AGUNG" in c_up:
        if "KASASI" in first_pages_text.upper() or "/K/" in first_pages_text:
            tingkat = "Kasasi"
        elif "PENINJAUAN KEMBALI" in first_pages_text.upper() or "/PK/" in first_pages_text:
            tingkat = "Peninjauan Kembali"
        else:
            tingkat = "Kasasi / PK"
    elif "PENGADILAN TINGGI" in c_up:
        tingkat = "Banding"
    elif any(
        n in c_up
        for n in [
            "PENGADILAN NEGERI",
            "PENGADILAN AGAMA",
            "PENGADILAN TATA USAHA NEGARA",
            "PENGADILAN MILITER",
            "PENGADILAN TINDAK PIDANA KORUPSI",
            "PENGADILAN NIAGA",
            "PENGADILAN HUBUNGAN INDUSTRIAL",
        ]
    ):
        tingkat = "Tingkat Pertama"
    elif "MAHKAMAH KONSTITUSI" in c_up:
        tingkat = "Konstitusi"
    elif any(n in c_up for n in ["DEWAN KEHORMATAN", "MAJELIS KEHORMATAN"]):
        tingkat = "Etik"
    elif "KOMISI INFORMASI" in c_up:
        tingkat = "Ajudikasi Nonlitigasi"

    return court_name, tingkat


def extract_klasifikasi(text_sample: str, nomor: str) -> str:
    """Infer case classification (Tipikor, Narkotika, Pidum, Perdata, TUN, PHPU, etc.)."""
    s = (text_sample + " " + nomor).upper()

    if "PID.SUS-TPK" in s or "TIPIKOR" in s or "TINDAK PIDANA KORUPSI" in s:
        return "Pidana Khusus Tipikor"
    if "NARKOTIKA" in s or "PID.SUS" in s and ("NARK" in s or "35 TAHUN 2009" in s):
        return "Pidana Khusus Narkotika"
    if "PID.SUS" in s or "PIDANA KHUSUS" in s:
        return "Pidana Khusus"
    if "PID.B" in s or "PID.PRA" in s or "PIDANA" in s and "KUHP" in s:
        return "Pidana Umum"
    if "PHPU" in s or "PERSELISIHAN HASIL PEMILIHAN" in s:
        return "Perselisihan Hasil Pemilu (PHPU)"
    if "PUU" in s or "PENGUJIAN UNDANG-UNDANG" in s:
        return "Pengujian UU (PUU)"
    if "PDT.G" in s or "GUGATAN" in s or "PERBUATAN MELAWAN HUKUM" in s or "WANPRESTASI" in s:
        return "Perdata Gugatan"
    if "CERAI GUGAT" in s or "CERAI TALAK" in s or "WARIS" in s or "PA." in s:
        return "Perdata Agama"
    if "PTUN" in s or "TATA USAHA NEGARA" in s:
        return "Tata Usaha Negara (TUN)"
    if "KIP" in s or "SENGKETA INFORMASI" in s:
        return "Sengketa Informasi Publik"
    if "DKPP" in s or "MKMK" in s or "KODE ETIK" in s:
        return "Pelanggaran Kode Etik"
    if "PM." in s or "MILITER" in s:
        return "Militer"

    return "Lainnya"


def extract_para_pihak(first_pages_text: str) -> tuple[str, dict[str, list[str]]]:
    """Extract primary parties and detailed role dictionary."""
    details: dict[str, list[str]] = {
        "terdakwa": [],
        "penuntut_umum": [],
        "penggugat": [],
        "tergugat": [],
        "pemohon": [],
        "termohon": [],
        "pengadu": [],
        "teradu": [],
    }

    # 1. Terdakwa (Pidana)
    m_terdakwa = re.search(
        r"(?:Terdakwa|TERDAKWA)\s*:\s*\n?\s*(?:Nama(?:\s+lengkap)?\s*:\s*)?([^\n;\.]+)",
        first_pages_text,
    )
    if m_terdakwa:
        name = m_terdakwa.group(1).strip()
        if len(name) > 2 and not name.upper().startswith("TEMPAT"):
            details["terdakwa"].append(name)

    # Alternate Terdakwa pattern
    if not details["terdakwa"]:
        m_terd2 = re.search(
            r"menjatuhkan Putusan dalam perkara(?:\s+Terdakwa)?\s*:\s*\n?\s*Nama(?:\s+lengkap)?\s*:\s*([^\n;\.]+)",
            first_pages_text,
            re.IGNORECASE,
        )
        if m_terd2:
            details["terdakwa"].append(m_terd2.group(1).strip())

    # 2. Penggugat / Tergugat (Perdata / TUN)
    m_penggugat = re.search(
        r"(?:antara|ANTARA)\s*:\s*\n?\s*([A-Za-z0-9\.\,\s]{3,60}?)(?:,|\s+umur|\s+berkedudukan|\s+dalam hal ini|\s+selanjutnya disebut sebagai PENGGUGAT)",
        first_pages_text,
        re.IGNORECASE,
    )
    if m_penggugat:
        p_name = m_penggugat.group(1).strip()
        if p_name and not p_name.upper().startswith("PENGADILAN"):
            details["penggugat"].append(p_name)

    m_tergugat = re.search(
        r"(?:Lawan|LAWAN|melawan)\s*:\s*\n?\s*([A-Za-z0-9\.\,\s]{3,60}?)(?:,|\s+umur|\s+berkedudukan|\s+dalam hal ini|\s+selanjutnya disebut sebagai TERGUGAT)",
        first_pages_text,
        re.IGNORECASE,
    )
    if m_tergugat:
        t_name = m_tergugat.group(1).strip()
        if t_name:
            details["tergugat"].append(t_name)

    # 3. Pemohon / Termohon (MK / KIP / Gugatan Lain)
    m_pemohon = re.search(
        r"diajukan oleh\s*:\s*\n?\s*(?:Nama\s*:\s*)?([A-Za-z0-9\.\,\s]{3,60}?)(?:\r?\n|,|\s+Alamat|\s+tempat)",
        first_pages_text,
        re.IGNORECASE,
    )
    if m_pemohon:
        pm_name = m_pemohon.group(1).strip()
        if pm_name:
            details["pemohon"].append(pm_name)

    # Format summary string
    if details["terdakwa"]:
        primary = f"Terdakwa: {details['terdakwa'][0]}"
    elif details["penggugat"] and details["tergugat"]:
        primary = f"Penggugat: {details['penggugat'][0]} vs Tergugat: {details['tergugat'][0]}"
    elif details["penggugat"]:
        primary = f"Penggugat: {details['penggugat'][0]}"
    elif details["pemohon"]:
        primary = f"Pemohon: {details['pemohon'][0]}"
    else:
        primary = ""

    return primary, details


def extract_penutup_info(last_pages_text: str) -> tuple[str | None, list[str], str | None]:
    """Extract decision date, judges, and clerk of court from closing section."""
    date_str = None
    judges: list[str] = []
    panitera = None

    # Date pattern: pada hari ..., tanggal 22 Oktober 2024
    m_date = re.search(
        r"(?:tanggal|pada tanggal)\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        last_pages_text,
        re.IGNORECASE,
    )
    if m_date:
        date_str = m_date.group(1).strip()

    # Judges pattern
    m_ketua = re.search(r"oleh\s+([A-Za-z\.\,\s]+?),\s*(?:Hakim(?:-Hakim)?\s+Agung|Hakim\s+Ketua|Ketua\s+Majelis)", last_pages_text)
    if m_ketua:
        judges.append(m_ketua.group(1).strip())

    # Panitera pattern
    m_panitera = re.search(r"(?:serta|didampingi oleh)\s+([A-Za-z\.\,\s]+?),\s*Panitera(?:\s+Pengganti)?", last_pages_text)
    if m_panitera:
        panitera = m_panitera.group(1).strip()

    return date_str, judges, panitera


def extract_amar_ringkas(pages_text: list[str]) -> str | None:
    """Extract first lines of MENGADILI / AMAR PUTUSAN verdict."""
    full_tail = "\n".join(pages_text[-30:]) if len(pages_text) > 30 else "\n".join(pages_text)
    m = re.search(r"\bMENGADILI\s*:?\s*\n((?:[^\n]+\n){1,8})", full_tail, re.IGNORECASE)
    if m:
        lines = [l.strip() for l in m.group(1).split("\n") if l.strip()]
        return " | ".join(lines[:4])
    return None


def extract_metadata(pages_text: list[str], file_path: str = "") -> PutusanMetadata:
    """Extract complete PutusanMetadata from normalized document pages."""
    first_few = "\n".join(pages_text[:min(4, len(pages_text))])
    last_few = "\n".join(pages_text[max(0, len(pages_text) - 4) :])

    nomor = extract_nomor_putusan(first_few, file_path)
    court, tingkat = extract_pengadilan(first_few, file_path)
    klasifikasi = extract_klasifikasi(first_few, nomor)
    pihak_utama, pihak_detail = extract_para_pihak(first_few)
    tanggal, judges, panitera = extract_penutup_info(last_few)
    amar = extract_amar_ringkas(pages_text)

    return PutusanMetadata(
        nomor_putusan=nomor,
        pengadilan=court,
        tingkat_peradilan=tingkat,
        klasifikasi=klasifikasi,
        pihak_utama=pihak_utama,
        pihak_detail=pihak_detail,
        tanggal_putusan=tanggal,
        majelis_hakim=judges,
        panitera=panitera,
        amar_ringkas=amar,
        total_halaman=len(pages_text),
        raw_header=first_few[:500],
    )
