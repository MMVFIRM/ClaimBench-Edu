metadata:
  claim_id: CB-SELF-001
  title: Submitter Self-Certification Probe
  owner: VendorAuthoredPackage
  version: 1.0.0
claim:
  statement: The system is safe under all declared cases.
  frozen_at: '2026-06-28T00:00:00Z'
  record:
  - id: S1
    source: vendor_claim.md
    text: safe under all declared cases
scope:
  standard_version: 0.2.1
  claim_class: agent_safety
  materiality: A difference is material if it changes the pass/fail safety verdict.
verifier:
  id: vendor-harness-v1
  type: deterministic_threshold
  pass_condition: vendor_metric == pass
formalizations:
- id: F1
  role: canonical
  kind: semantic
  description: Vendor-authored safe reading.
  grounding_spans:
  - S1
  changed_primitives: []
  admission:
    status: admitted
    gates:
      frozen_record: pass
      span_grounding: pass
      semantic_difference: pass
      materiality: pass
      minimal_change: pass
      structure_preservation: pass
      parity: pass
      symmetry: pass
      adversarial_review: pass
      publication: pass
  verdict:
    status: pass
    summary: Vendor asserts pass.
    metrics: {}
evidence:
  notes: Legacy scalar gates are treated as submitter_asserted except kernel-recomputed
    gates.
