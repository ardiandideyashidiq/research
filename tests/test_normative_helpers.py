from __future__ import annotations

import tempfile
from pathlib import Path

from research.app import ResearchApp
from research.db.models import PublicationRecord


def test_workflow_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_pub.sqlite"
        app = ResearchApp(db_path=db_path)

        # 1. Init project
        proj = app.workflow.init_project(
            title="Pertanggungjawaban Pidana AI di Indonesia",
            author="Budi Santoso",
            typology="wet_vacuum",
            approaches=["statute", "conceptual", "comparative"],
            research_questions=[
                "Bagaimana kualifikasi perbuatan AI dalam hukum pidana?",
                "Bagaimana formulasi preskripsi pertanggungjawaban hukum pengembang AI?",
            ],
        )
        assert proj.title == "Pertanggungjawaban Pidana AI di Indonesia"
        assert proj.current_stage == 1
        assert proj.completed_count() == 0

        # 2. Check stages
        proj = app.workflow.check_stage(
            stage_num=1,
            passed=True,
            notes="Isu murni masalah norma ketiadaan subjek hukum AI",
        )
        assert proj.is_stage_completed(1)
        assert proj.current_stage == 2

        # Check stage 6 with metadata
        proj = app.workflow.check_stage(
            stage_num=6,
            passed=True,
            notes="Konstruksi teori berjenjang selesai",
            metadata={
                "grand_theory": "Teori Keadilan Substantif",
                "middle_theory": "Teori Kebijakan Kriminal",
                "applied_theory": "Teori Strict Liability",
            },
        )
        assert proj.is_stage_completed(6)
        assert proj.grand_theory == "Teori Keadilan Substantif"

        # 3. Dashboard rendering
        dashboard = app.workflow.render_status_dashboard()
        assert "DASHBOARD PROGRES RISET HUKUM NORMATIF" in dashboard
        assert "Pertanggungjawaban Pidana AI di Indonesia" in dashboard
        assert "Teori Keadilan Substantif" in dashboard

        # 4. Export audit
        audit_file = Path(tmp_dir) / "audit.md"
        exported = app.workflow.export_methodology_audit(audit_file)
        assert exported.exists()
        content = exported.read_text(encoding="utf-8")
        assert "Laporan Audit Metodologi Riset Hukum Normatif" in content
        assert "Teori Strict Liability" in content

        app.close_sync()


def test_irac_syllogisms_and_analogy_guard() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_pub.sqlite"
        app = ResearchApp(db_path=db_path)

        # 1. Valid syllogism
        syl1 = app.irac.add_syllogism(
            issue="Apakah AI memenuhi kualifikasi barang imateriel?",
            rule_major="Pasal 362 KUHP mensyaratkan unsur 'mengambil barang yang seluruhnya atau sebagian kepunyaan orang lain'.",
            facts_minor="Terdakwa menyedot kode algoritma hak cipta korban secara tanpa hak.",
            conclusion="Kode algoritma terkualifikasi sebagai barang imateriel yang dapat menjadi objek tindak pidana pencurian.",
            research_question_idx=1,
            legal_domain="pidana",
            method_type="interpretasi_teleologis",
            cite_keys=["Santoso2025AI"],
        )
        warns1 = syl1.validate_logic()
        assert len(warns1) == 0

        # 2. Syllogism violating criminal law analogy prohibition (Tahap 15)
        syl_invalid = app.irac.add_syllogism(
            issue="Apakah AI dapat dipidana langsung seperti orang?",
            rule_major="Pasal 55 KUHP mengatur penyertaan orang perorangan.",
            facts_minor="Sistem AI melakukan eksekusi transaksi ilegal secara mandiri.",
            conclusion="Sistem AI dipidana dengan menganalogikannya sebagai subjek hukum orang.",
            research_question_idx=1,
            legal_domain="pidana",
            method_type="analogi",  # VIOLATION in Criminal Law
        )
        warns2 = syl_invalid.validate_logic()
        assert len(warns2) > 0
        assert any("Analogi dilarang keras dalam Hukum Pidana" in w for w in warns2)

        # 3. List and validate all
        all_syls = app.irac.list_syllogisms()
        assert len(all_syls) == 2

        all_warns = app.irac.validate_all()
        assert syl_invalid.syllogism_id in all_warns

        # 4. Export markdown
        md_export = app.irac.export_irac_markdown()
        assert (
            "#### IRAC: Apakah AI memenuhi kualifikasi barang imateriel?" in md_export
        )
        assert "Premis Mayor" in md_export

        app.close_sync()


def test_thesis_scaffolder_and_traceability_auditor() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_pub.sqlite"
        draft_dir = Path(tmp_dir) / "draft_skripsi"
        app = ResearchApp(db_path=db_path)

        # Populate a sample publication in DB
        pub = PublicationRecord(
            cite_key="Santoso2025AI",
            title="Kecerdasan Buatan dan Hukum",
            authors=["Budi Santoso"],
            year=2025,
            journal="Jurnal Hukum",
        )
        app.db.create(pub)

        # Init project & IRAC
        app.workflow.init_project(
            title="Rekonstruksi Hukum Siber",
            author="Ahmad Fauzi",
            research_questions=[
                "Bagaimana status hukum agen otonom?",
                "Bagaimana regulasi perlindungan data pribadi?",
            ],
        )
        app.irac.add_syllogism(
            issue="Status hukum agen otonom",
            rule_major="Pasal 1 angka 1 UU ITE",
            facts_minor="Agen cerdas bertindak atas delegasi pengguna",
            conclusion="Agen otonom bertindak sebagai agen elektronik",
            research_question_idx=1,
            cite_keys=["Santoso2025AI"],
        )

        # 1. Scaffold 5-chapter draft
        files = app.scaffolder.generate_draft(
            output_dir=draft_dir,
            style="indonesia",
        )
        assert "bab1" in files
        assert "bab2" in files
        assert "bab_3" in files
        assert "bab_4" in files
        assert "penutup" in files
        assert "daftar_pustaka" in files

        # Check content
        bab1_text = files["bab1"].read_text(encoding="utf-8")
        assert "Rekonstruksi Hukum Siber" in bab1_text
        assert "PIRAMIDA TERBALIK" in bab1_text

        bab3_text = files["bab_3"].read_text(encoding="utf-8")
        assert "IRAC: Status hukum agen otonom" in bab3_text

        # 2. Add an intentional citation in bab1
        files["bab1"].write_text(
            bab1_text
            + "\nMenurut rujukan @Santoso2025AI dan @GhostKey2025, hal ini krusial.\n",
            encoding="utf-8",
        )

        # 3. Run Traceability Auditor
        report = app.auditor.audit_drafts(draft_dir=draft_dir)
        assert report.total_files_scanned > 0
        assert "Santoso2025AI" in report.verified_cite_keys
        assert "GhostKey2025" in report.ghost_cite_keys
        assert len(report.warnings) > 0

        md_rep = report.to_markdown()
        assert "Laporan Audit Traceability" in md_rep
        assert "GhostKey2025" in md_rep

        app.close_sync()


if __name__ == "__main__":
    test_workflow_lifecycle()
    test_irac_syllogisms_and_analogy_guard()
    test_thesis_scaffolder_and_traceability_auditor()
    print("All normative helper tests passed successfully!")
