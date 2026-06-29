metadata:
  claim_id: CB-GAP-001
  title: Refuted Claim With Evidentiary Gap
  owner: ExampleLab
  version: 1.0.0
claim:
  statement: Method C beats the declared baseline on Task Q.
  frozen_at: '2026-06-28T00:00:00Z'
  record:
  - id: S1
    source: paper.md
    text: Method C beats the declared baseline on Task Q.
  - id: S2
    source: eval_card.md
    text: Task Q is measured by accuracy over the declared test split.
scope:
  standard_version: 0.2.1
  claim_class: model_improvement
  materiality: A difference is material if it changes whether accuracy_delta is greater
    than zero outside uncertainty bounds.
verifier:
  id: task-q-accuracy-v1
  type: statistical_threshold
  pass_condition: lower_confidence_bound(accuracy_delta) > 0
formalizations:
- id: F1
  role: canonical
  kind: semantic
  description: Method C must improve accuracy over the declared baseline on Task Q.
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
    status: fail
    summary: Accuracy delta is negative on the declared test split.
    metrics:
      accuracy_delta: -0.012
      ci_low: -0.024
      ci_high: -0.001
- id: F2
  role: alternative
  kind: evidentiary
  description: A smaller follow-up run is underpowered and cannot separate the result
    from zero.
  grounding_spans:
  - S1
  - S2
  changed_primitives:
  - sample_size
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
    summary: Small follow-up run crosses zero but does not overturn the declared failing
      run.
    metrics:
      accuracy_delta: 0.003
      ci_low: -0.02
      ci_high: 0.026
      n: 80
evidence:
  notes: Demonstrates that inconclusive evidence does not erase a fail.
