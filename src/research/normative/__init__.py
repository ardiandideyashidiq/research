from __future__ import annotations

from research.normative.irac import IRACManager
from research.normative.models import (
    PHASE_DEFINITIONS,
    STAGE_DEFINITIONS,
    AuditReport,
    LegalSyllogism,
    NormativeProject,
)
from research.normative.scaffold import ThesisScaffolder
from research.normative.traceability import TraceabilityAuditor
from research.normative.workflow import WorkflowManager

__all__ = [
    "PHASE_DEFINITIONS",
    "STAGE_DEFINITIONS",
    "AuditReport",
    "IRACManager",
    "LegalSyllogism",
    "NormativeProject",
    "ThesisScaffolder",
    "TraceabilityAuditor",
    "WorkflowManager",
]
