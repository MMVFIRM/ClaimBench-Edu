from enum import Enum


class Badge(str, Enum):
    VERIFIED = "Verified"
    REFUTED = "Refuted"
    REFUTED_WITH_EVIDENTIARY_GAPS = "Refuted with Evidentiary Gaps"
    SEMANTIC_BOUNDARY = "Semantic Boundary"
    EVIDENTIARY_INCONCLUSIVE = "Evidentiary Inconclusive"
    OUT_OF_SCOPE = "Out of Scope"
    SELF_ATTESTED_ONLY = "Self-Attested Only"


BADGE_EXPLANATIONS = {
    Badge.VERIFIED: "All certified, admitted materially faithful semantic formalizations pass.",
    Badge.REFUTED: "All certified, admitted materially faithful semantic formalizations fail.",
    Badge.REFUTED_WITH_EVIDENTIARY_GAPS: "At least one certified admitted reading fails, no certified admitted reading passes, and one or more admitted readings or evidence channels are inconclusive.",
    Badge.SEMANTIC_BOUNDARY: "Certified admitted faithful semantic formalizations diverge between pass and fail.",
    Badge.EVIDENTIARY_INCONCLUSIVE: "Meaning is stable, but certified evidence is insufficient to support pass or fail.",
    Badge.OUT_OF_SCOPE: "No certified admissible semantic formalization exists under the declared standard and scope.",
    Badge.SELF_ATTESTED_ONLY: "The package contains only submitter-asserted or LLM-proposed gate support for one or more certification-critical gates; no ClaimBench badge is issued.",
}
