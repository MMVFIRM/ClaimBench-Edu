metadata:
  claim_id: CB-EVID-001
  title: Underpowered Improvement Claim
  owner: ExampleLab
  version: 1.0.0
claim:
  statement: Method B improves benchmark accuracy over the baseline on Task Z.
  frozen_at: '2026-06-28T00:00:00Z'
  record:
  - id: S1
    source: paper.md
    text: Method B improves benchmark accuracy over the baseline on Task Z.
  - id: S2
    source: eval_card.md
    text: Task Z is measured by top-1 accuracy.
scope:
  standard_version: 0.2.1
  claim_class: model_improvement
  materiality: A difference is material if it changes whether accuracy_delta is greater
    than zero outside uncertainty bounds.
verifier:
  id: task-z-accuracy-v1
  type: statistical_threshold
  pass_condition: lower_confidence_bound(accuracy_delta) > 0
formalizations:
- id: F1
  role: canonical
  kind: semantic
  description: Method B must improve top-1 accuracy over baseline on Task Z.
  grounding_spans:
  - S1
  - S2
  changed_primitives: []
  admission:
    status: admitted
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
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      materiality:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      minimal_change:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      structure_preservation:
        status: pass
        source: claimbench_adjudicated
        producer: claimbench_standard_v0.2.1_demo
        reason: ''
      parity:
        status: pass
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
    summary: Observed delta is positive but confidence interval crosses zero.
    metrics:
      observed_accuracy_delta: 0.006
      ci_low: -0.004
      ci_high: 0.016
      n: 200
evidence:
  artifacts: examples/artifacts/task_z_small_sample.csv
  notes: Meaning is stable; evidence is underpowered.
