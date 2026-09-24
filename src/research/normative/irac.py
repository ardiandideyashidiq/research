from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from research.normative.models import LegalSyllogism

if TYPE_CHECKING:
    from research.db.manager import DatabaseManager


class IRACManager:
    """Manager for deductive legal syllogisms and IRAC argumentation structure stored in SQLite."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add_syllogism(
        self,
        issue: str,
        rule_major: str,
        facts_minor: str,
        conclusion: str,
        *,
        research_question_idx: int = 1,
        legal_domain: str = "umum",
        method_type: str = "interpretasi_gramatikal",
        cite_keys: list[str] | None = None,
        project_id: str = "default",
        syllogism_id: str | None = None,
    ) -> LegalSyllogism:
        """Create and store a legal syllogism (IRAC) record."""
        now = datetime.now(UTC).isoformat()
        s_id = syllogism_id or f"syl_{uuid.uuid4().hex[:8]}"
        syl = LegalSyllogism(
            syllogism_id=s_id,
            project_id=project_id,
            research_question_idx=research_question_idx,
            issue=issue,
            rule_major=rule_major,
            facts_minor=facts_minor,
            conclusion=conclusion,
            legal_domain=legal_domain,
            method_type=method_type,
            cite_keys=cite_keys or [],
            created_at=now,
            updated_at=now,
        )

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO legal_syllogisms(
                syllogism_id, project_id, research_question_idx, issue, rule_major, facts_minor,
                legal_domain, method_type, conclusion, cite_keys, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                syl.syllogism_id,
                syl.project_id,
                syl.research_question_idx,
                syl.issue,
                syl.rule_major,
                syl.facts_minor,
                syl.legal_domain,
                syl.method_type,
                syl.conclusion,
                json.dumps(syl.cite_keys),
                syl.created_at,
                syl.updated_at,
            ),
        )
        conn.commit()
        logger.info(f"Added legal syllogism '{s_id}' for issue '{issue[:40]}...'")
        return syl

    def get_syllogism(self, syllogism_id: str) -> LegalSyllogism | None:
        """Get single syllogism by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT * FROM legal_syllogisms WHERE syllogism_id = ?",
            (syllogism_id,),
        ).fetchone()
        if not row:
            return None
        return LegalSyllogism.from_row(dict(row))

    def list_syllogisms(
        self,
        project_id: str = "default",
        question_idx: int | None = None,
    ) -> list[LegalSyllogism]:
        """List syllogisms for a project, optionally filtered by research question index."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if question_idx is not None:
            rows = cursor.execute(
                "SELECT * FROM legal_syllogisms WHERE project_id = ? AND research_question_idx = ? ORDER BY created_at ASC",
                (project_id, question_idx),
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM legal_syllogisms WHERE project_id = ? ORDER BY research_question_idx ASC, created_at ASC",
                (project_id,),
            ).fetchall()
        return [LegalSyllogism.from_row(dict(r)) for r in rows]

    def delete_syllogism(self, syllogism_id: str) -> bool:
        """Delete syllogism by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM legal_syllogisms WHERE syllogism_id = ?", (syllogism_id,)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

    def validate_all(self, project_id: str = "default") -> dict[str, list[str]]:
        """Validate all syllogisms for a project against logic and legal rules."""
        syllogisms = self.list_syllogisms(project_id=project_id)
        report: dict[str, list[str]] = {}
        for s in syllogisms:
            warns = s.validate_logic()
            if warns:
                report[s.syllogism_id] = warns
        return report

    def export_irac_markdown(
        self,
        project_id: str = "default",
        question_idx: int | None = None,
        output_path: str | Path | None = None,
    ) -> str:
        """Render all syllogisms formatted in IRAC sections ready for Bab III / IV."""
        syllogisms = self.list_syllogisms(
            project_id=project_id, question_idx=question_idx
        )
        if not syllogisms:
            return "*(Belum ada unit silogisme IRAC yang terdaftar)*\n"

        blocks: list[str] = [
            f"# Matriks Penalaran Hukum Deduktif (IRAC Blocks) - Proyek `{project_id}`",
            f"*Total Unit Penalaran*: {len(syllogisms)}",
            "",
        ]

        curr_q = None
        for s in syllogisms:
            if s.research_question_idx != curr_q:
                curr_q = s.research_question_idx
                blocks.append(f"\n### Pembahasan Rumusan Masalah {curr_q}\n")
            blocks.append(s.to_irac_markdown())

        content = "\n".join(blocks)
        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            logger.info(f"Exported IRAC markdown to {p}")

        return content
