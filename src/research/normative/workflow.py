from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from research.normative.models import (
    PHASE_DEFINITIONS,
    STAGE_DEFINITIONS,
    NormativeProject,
)

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager


class WorkflowManager:
    """Manager for normative legal research project state, 20-stage progress, and gate checks."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def init_project(
        self,
        title: str,
        author: str = "",
        typology: str = "",
        approaches: list[str] | None = None,
        research_questions: list[str] | None = None,
        project_id: str = "default",
    ) -> NormativeProject:
        """Create or overwrite the active normative research project."""
        now = datetime.now(UTC).isoformat()
        proj = NormativeProject(
            project_id=project_id,
            title=title,
            author=author,
            typology=typology,
            approaches=approaches or [],
            research_questions=research_questions or [],
            created_at=now,
            updated_at=now,
        )
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO normative_projects(
                project_id, title, author, typology, approaches, research_questions,
                grand_theory, middle_theory, applied_theory, principles,
                current_stage, gate_checks, stage_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proj.project_id,
                proj.title,
                proj.author,
                proj.typology,
                json.dumps(proj.approaches),
                json.dumps(proj.research_questions),
                proj.grand_theory,
                proj.middle_theory,
                proj.applied_theory,
                json.dumps(proj.principles),
                proj.current_stage,
                json.dumps(proj.gate_checks),
                json.dumps(proj.stage_notes),
                proj.created_at,
                proj.updated_at,
            ),
        )
        conn.commit()
        logger.info(
            f"Initialized normative research project '{title}' (ID: {project_id})"
        )
        return proj

    def get_project(self, project_id: str = "default") -> NormativeProject | None:
        """Retrieve project by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT * FROM normative_projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        return NormativeProject.from_row(dict(row))

    def update_project(
        self,
        project_id: str = "default",
        *,
        title: str | None = None,
        author: str | None = None,
        typology: str | None = None,
        approaches: list[str] | None = None,
        research_questions: list[str] | None = None,
        grand_theory: str | None = None,
        middle_theory: str | None = None,
        applied_theory: str | None = None,
        principles: list[str] | None = None,
        current_stage: int | None = None,
    ) -> NormativeProject:
        """Update selective project fields."""
        proj = self.get_project(project_id)
        if not proj:
            proj = self.init_project(
                title=title or "Skripsi Riset Hukum",
                author=author or "",
                project_id=project_id,
            )

        if title is not None:
            proj.title = title
        if author is not None:
            proj.author = author
        if typology is not None:
            proj.typology = typology
        if approaches is not None:
            proj.approaches = approaches
        if research_questions is not None:
            proj.research_questions = research_questions
        if grand_theory is not None:
            proj.grand_theory = grand_theory
        if middle_theory is not None:
            proj.middle_theory = middle_theory
        if applied_theory is not None:
            proj.applied_theory = applied_theory
        if principles is not None:
            proj.principles = principles
        if current_stage is not None:
            proj.current_stage = max(1, min(20, current_stage))

        proj.updated_at = datetime.now(UTC).isoformat()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE normative_projects SET
                title = ?, author = ?, typology = ?, approaches = ?, research_questions = ?,
                grand_theory = ?, middle_theory = ?, applied_theory = ?, principles = ?,
                current_stage = ?, gate_checks = ?, stage_notes = ?, updated_at = ?
            WHERE project_id = ?
            """,
            (
                proj.title,
                proj.author,
                proj.typology,
                json.dumps(proj.approaches),
                json.dumps(proj.research_questions),
                proj.grand_theory,
                proj.middle_theory,
                proj.applied_theory,
                json.dumps(proj.principles),
                proj.current_stage,
                json.dumps(proj.gate_checks),
                json.dumps(proj.stage_notes),
                proj.updated_at,
                proj.project_id,
            ),
        )
        conn.commit()
        return proj

    def check_stage(
        self,
        stage_num: int,
        passed: bool = True,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
        project_id: str = "default",
    ) -> NormativeProject:
        """Record gate check status for a specific stage (1-20)."""
        if stage_num < 1 or stage_num > 20:
            msg = f"Invalid stage number: {stage_num}. Must be 1 to 20."
            raise ValueError(msg)

        proj = self.get_project(project_id)
        if not proj:
            proj = self.init_project("Skripsi Riset Hukum", project_id=project_id)

        proj.gate_checks[str(stage_num)] = passed
        if notes:
            proj.stage_notes[str(stage_num)] = notes

        # Merge stage-specific metadata
        if metadata:
            if metadata.get("typology"):
                proj.typology = metadata["typology"]
            if metadata.get("approaches"):
                proj.approaches = metadata["approaches"]
            if metadata.get("research_questions"):
                proj.research_questions = metadata["research_questions"]
            if metadata.get("grand_theory"):
                proj.grand_theory = metadata["grand_theory"]
            if metadata.get("middle_theory"):
                proj.middle_theory = metadata["middle_theory"]
            if metadata.get("applied_theory"):
                proj.applied_theory = metadata["applied_theory"]
            if metadata.get("principles"):
                proj.principles = metadata["principles"]

        # Advance active stage automatically if passed
        if passed and stage_num == proj.current_stage and stage_num < 20:
            proj.current_stage = stage_num + 1

        proj.updated_at = datetime.now(UTC).isoformat()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE normative_projects SET
                typology = ?, approaches = ?, research_questions = ?,
                grand_theory = ?, middle_theory = ?, applied_theory = ?, principles = ?,
                current_stage = ?, gate_checks = ?, stage_notes = ?, updated_at = ?
            WHERE project_id = ?
            """,
            (
                proj.typology,
                json.dumps(proj.approaches),
                json.dumps(proj.research_questions),
                proj.grand_theory,
                proj.middle_theory,
                proj.applied_theory,
                json.dumps(proj.principles),
                proj.current_stage,
                json.dumps(proj.gate_checks),
                json.dumps(proj.stage_notes),
                proj.updated_at,
                proj.project_id,
            ),
        )
        conn.commit()
        return proj

    def render_status_dashboard(self, project_id: str = "default") -> str:
        """Render a terminal-friendly dashboard showing progress across 7 phases & 20 stages."""
        proj = self.get_project(project_id)
        if not proj:
            return f"[!] Belum ada proyek riset aktif (ID: '{project_id}'). Jalankan 'research workflow init <title>' untuk memulai."

        pct = proj.progress_percentage()
        completed = proj.completed_count()

        lines = [
            "=" * 78,
            f" ⚖️  DASHBOARD PROGRES RISET HUKUM NORMATIF: {proj.title}",
            f" Peneliti: {proj.author or '—'} | Progres: {completed}/20 Tahap ({pct:.1f}%)",
            "=" * 78,
            "",
        ]

        if proj.typology:
            lines.append(f"• Tipologi Norma  : {proj.typology.upper()}")
        if proj.approaches:
            lines.append(
                f"• Pendekatan      : {', '.join(a.title() for a in proj.approaches)}"
            )
        if proj.grand_theory or proj.middle_theory or proj.applied_theory:
            lines.append(
                f"• Teori 3-Tier    : Grand: {proj.grand_theory or '—'} | Middle: {proj.middle_theory or '—'} | Applied: {proj.applied_theory or '—'}"
            )
        if proj.research_questions:
            lines.append(
                f"• Rumusan Masalah : {len(proj.research_questions)} butir terdaftar"
            )
        lines.append("")

        for phase_code, phase_info in PHASE_DEFINITIONS.items():
            stages = phase_info["stages"]
            phase_completed = sum(1 for s in stages if proj.is_stage_completed(s))
            phase_status = (
                "✅"
                if phase_completed == len(stages)
                else ("🔄" if phase_completed > 0 else "⏳")
            )

            lines.append(
                f"{phase_status} FASE {phase_code}: {phase_info['title']} ({phase_completed}/{len(stages)} Selesai)"
            )
            lines.append("-" * 78)

            for s in stages:
                s_info = STAGE_DEFINITIONS[s]
                is_done = proj.is_stage_completed(s)
                is_current = s == proj.current_stage

                tag = (
                    "[DONE]" if is_done else ("[ACTIVE]" if is_current else "[PENDING]")
                )
                symbol = "✔️" if is_done else ("👉" if is_current else "⚪")
                lines.append(f"  {symbol} Tahap {s:02d}: {s_info['title']} {tag}")

                notes = proj.stage_notes.get(str(s))
                if notes:
                    lines.append(f"     └─ Catatan: {notes}")
            lines.append("")

        lines.append("=" * 78)
        lines.append(
            f"Tahap Aktif Saat Ini: Tahap {proj.current_stage}: {STAGE_DEFINITIONS[proj.current_stage]['title']}"
        )
        lines.append(
            f"Ceklis Kunci: {STAGE_DEFINITIONS[proj.current_stage]['checklist'][0]}"
        )
        lines.append(
            "Jalankan: 'research workflow check <stage_num> --pass --notes \"...\"' untuk memperbarui."
        )
        lines.append("=" * 78)

        return "\n".join(lines)

    def export_methodology_audit(
        self,
        output_path: str | Path | None = None,
        project_id: str = "default",
    ) -> Path:
        """Export comprehensive methodological audit trail markdown document."""
        proj = self.get_project(project_id)
        if not proj:
            msg = f"Project '{project_id}' not found."
            raise ValueError(msg)

        path = Path(output_path) if output_path else Path("logs/metodologi_audit.md")
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Laporan Audit Metodologi Riset Hukum Normatif: {proj.title}",
            f"**Peneliti**: {proj.author or '—'} | **Terakhir Diperbarui**: {proj.updated_at}",
            f"**Tingkat Kelengkapan Metodologis**: {proj.completed_count()}/20 Tahap ({proj.progress_percentage():.1f}%)",
            "",
            "## I. Parameter Riset Dasar",
            f"- **Tipologi Problematika Norma**: `{proj.typology or 'Belum ditentukan'}`",
            f"- **Pendekatan Penelitian**: {', '.join(f'`{a}`' for a in proj.approaches) if proj.approaches else 'Belum ditentukan'}",
            "- **Kerangka Teori 3-Tier**:",
            f"  - *Grand Theory*: {proj.grand_theory or '—'}",
            f"  - *Middle Range Theory*: {proj.middle_theory or '—'}",
            f"  - *Applied Theory*: {proj.applied_theory or '—'}",
            f"- **Asas-Asas Hukum Terpetakan**: {', '.join(proj.principles) if proj.principles else '—'}",
            "",
            "## II. Rumusan Masalah Akademis",
        ]

        if proj.research_questions:
            for idx, q in enumerate(proj.research_questions, start=1):
                lines.append(f"{idx}. {q}")
        else:
            lines.append("*(Belum ada rumusan masalah terdaftar)*")
        lines.append("")

        lines.append("## III. Matriks Evaluasi 20 Tahap (Gate-Checks)")
        lines.append("")
        lines.append("| Tahap | Nama Tahap | Status | Catatan / Bukti Operasional |")
        lines.append("|:---:|:---|:---:|:---|")

        for s in range(1, 21):
            s_info = STAGE_DEFINITIONS[s]
            status_badge = "✅ Selesai" if proj.is_stage_completed(s) else "⏳ Belum"
            note = proj.stage_notes.get(str(s), "—").replace("|", "\\|")
            lines.append(f"| {s:02d} | {s_info['title']} | {status_badge} | {note} |")

        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Exported methodology audit to {path}")
        return path
