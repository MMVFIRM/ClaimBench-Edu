metadata:
  claim_id: CB-OOS-001
  title: General Intelligence Claim
  owner: ExampleAI
  version: 1.0.0
claim:
  statement: This model understands the world like a human.
  frozen_at: '2026-06-28T00:00:00Z'
  record:
  - id: S1
    source: landing_page.md
    text: understands the world like a human
scope:
  standard_version: 0.2.1
  claim_class: general
  materiality: No declared materiality threshold available for this claim class.
verifier:
  id: none
  type: none
  pass_condition: not applicable
formalizations:
- id: F1
  role: canonical
  kind: out_of_scope
  description: No admissible deterministic verifier or materiality threshold exists
    for the phrase 'understands the world like a human' under v0.1.
  grounding_spans:
  - S1
  changed_primitives: []
  admission:
    status: rejected
    reason: Claim is outside declared v0.1 claim classes and lacks measurable primitives.
    gates:
      frozen_record:
        status: pass
        source: kernel_recomputed
        producer: claimbench_kernel
        reason: ''
      span_grounding:
        status: pass
        source: kernel_recomputed
        producer: claimbench_kernel
        reason: ''
      semantic_difference:
        status: fail
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      materiality:
        status: fail
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      minimal_change:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      structure_preservation:
        status: fail
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      parity:
        status: fail
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      symmetry:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      adversarial_review:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      publication:
        status: pass
        source: kernel_recomputed
        producer: claimbench_kernel
        reason: ''
  verdict:
    status: inconclusive
    summary: Out of scope under ClaimBench Standard v0.1.
    metrics: {}
evidence:
  notes: Demo out-of-scope certificate.
