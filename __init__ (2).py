"""Real-corpus validation data model.

Three columns must never touch:

  1. EXTRACTION  — the structured evidence pulled from the paper. Carries a
     provenance field. If an LLM produced it, it must be human_verified before it
     can back a scored result. The procedure consumes ONLY this.
  2. PREDICTION  — what null_reconstructor produces from the extraction. The
     thing under test.
  3. GROUND TRUTH — the human label. The ONLY source of truth. Produced by a
     human reading the paper, never by a model.

The scorer compares PREDICTION against GROUND TRUTH. It must never read a
model-derived verdict into the truth column, and it must refuse to score a case
whose extraction is unverified, because a shared extraction error would flatter
the false-certify rate toward zero — the one bias that gets a bad key issued.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewStatus(str, Enum):
    SINGLE_REVIEWER = "single_reviewer_label"
    PANEL_CONFIRMED = "panel_confirmed_label"
    DISPUTED = "disputed_label"
    NEEDS_PANEL_REVIEW = "needs_panel_review"


class ExtractionProvenance(str, Enum):
    HUMAN = "human"
    HUMAN_VERIFIED = "human_verified"   # LLM-drafted, human-checked: acceptable
    LLM_UNVERIFIED = "llm_unverified"   # NOT acceptable for scoring
    UNKNOWN = "unknown"


# Extraction provenances that may back a scored, key-eligible result.
SCOREABLE_EXTRACTION = {ExtractionProvenance.HUMAN.value, ExtractionProvenance.HUMAN_VERIFIED.value}

# Review statuses that count as ground truth for a scored result.
TRUTH_STATUSES = {ReviewStatus.SINGLE_REVIEWER.value, ReviewStatus.PANEL_CONFIRMED.value}

VALID_VERDICTS = {"pass", "fail", "semantic_boundary", "evidentiary_inconclusive", "out_of_scope"}


@dataclass
class PaperRecord:
    """Ingested paper + claim. The EXTRACTION column."""
    id: str
    paper_id: str            # e.g. arXiv id
    title: str
    claim_statement: str
    claim_class: str
    subclass: str
    evidence: Dict[str, Any]                 # method/baselines/budget/... (procedure input)
    evidence_spans: List[Dict[str, str]]     # verbatim spans backing the evidence
    extraction_provenance: str = ExtractionProvenance.UNKNOWN.value
    extracted_by: str = ""
    artifact_links: List[str] = field(default_factory=list)
    alternative_readings: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PaperRecord":
        return cls(
            id=str(d["id"]),
            paper_id=str(d.get("paper_id", "")),
            title=str(d.get("title", "")),
            claim_statement=str(d.get("claim_statement", "")),
            claim_class=str(d.get("claim_class", "")),
            subclass=str(d.get("subclass", "unknown")),
            evidence=dict(d.get("evidence", {}) or {}),
            evidence_spans=list(d.get("evidence_spans", []) or []),
            extraction_provenance=str(d.get("extraction_provenance", ExtractionProvenance.UNKNOWN.value)),
            extracted_by=str(d.get("extracted_by", "")),
            artifact_links=list(d.get("artifact_links", []) or []),
            alternative_readings=list(d.get("alternative_readings", []) or []),
        )

    @property
    def extraction_scoreable(self) -> bool:
        return self.extraction_provenance in SCOREABLE_EXTRACTION


@dataclass
class HumanLabel:
    """The GROUND TRUTH column. Must come from a human reviewer."""
    record_id: str
    verdict: str
    claim_class: str
    rationale: str
    confidence: str                  # high | medium | low
    reviewer_id: str
    review_status: str
    labeled_by_model: bool = False   # MUST be False to count as truth

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HumanLabel":
        return cls(
            record_id=str(d["record_id"]),
            verdict=str(d.get("verdict", "")),
            claim_class=str(d.get("claim_class", "")),
            rationale=str(d.get("rationale", "")),
            confidence=str(d.get("confidence", "")),
            reviewer_id=str(d.get("reviewer_id", "")),
            review_status=str(d.get("review_status", "")),
            labeled_by_model=bool(d.get("labeled_by_model", False)),
        )

    @property
    def is_ground_truth(self) -> bool:
        """A label is usable as truth only if a human produced it, it carries a
        valid decisive/abstaining verdict, and its review status is a truth
        status (single-reviewer or panel-confirmed). needs_panel_review and
        disputed are explicitly NOT truth."""
        return (
            not self.labeled_by_model
            and self.verdict in VALID_VERDICTS
            and self.review_status in TRUTH_STATUSES
        )
