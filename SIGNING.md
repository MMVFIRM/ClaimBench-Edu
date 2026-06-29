metadata:
  claim_id: geodistill-draft-001
  title: Draft GeoDistill claim from formalizer
  owner: MMV Firm
  version: 0.1.0
claim:
  statement: "GeoDistill outperforms standard distillation under the same compression budget."
  frozen_at: "2026-06-28T00:00:00Z"
  record:
    - id: S1
      source: draft_claim.md
      text: "GeoDistill outperforms standard distillation under the same compression budget."
    - id: S2
      source: experiment_notes.md
      text: "Compression budget may refer to stored-float budget or learned-parameter budget."
scope:
  standard_version: claimbench-standard-v0.2.1
  claim_class: comparative_empirical
  materiality: "A difference is material if it can change the issued badge or verifier verdict."
verifier:
  id: manual-geodistill-v0
  type: manual_placeholder
  pass_condition: "Formalizer drafts only; external verifier must supply pass/fail metrics."
evidence:
  artifact_status: draft
formalizer:
  provider: mock
  draft_verdict: inconclusive
