# ClaimBench v2.1 — conformance & adversarial harness (contribution)

Additive only. No existing files modified. Drop these in:

```
src/claimbench/conformance.py     # replay / reproduction verifier
redteam.py                        # adversarial conformance harness (runnable)
tests/test_conformance.py         # unit tests (hook into `unittest discover`)
```

Full suite after adding: `PYTHONPATH=src python -m unittest discover tests` → 16 pass
(your 12 + 4 new). Harness: `PYTHONPATH=src python redteam.py` → 6/6 defenses held.

## The finding this closes

`crypto.verify_certificate_dict` proves a signature is valid over the **stored**
`certificate_core`. It does not prove the core is the deterministic output of the
kernel on the claim package. Demonstrated forge:

1. Evaluate `model_improvement_refuted.yaml` → core badge `Refuted`.
2. Hand-edit the core: `badge = "Verified"`.
3. Re-sign with any key.
4. `verify-certificate` → **PASS**.

A valid signature attests *who signed*, not *that the badge follows from the
evidence*. Without a reproduction step, the signing layer secures the wrong
object, and a malicious or buggy issuer can mint a signed `Verified` over a claim
that refutes.

## What the contribution adds

**`conformance.py`** — three re-derivation checks, strongest first:

- `badge_self_consistent` — recomputes the badge purely from the formalizations
  the core already embeds (kind, verdict, certified/asserted flags) and requires
  it to equal the stored badge. **Catches the forge from the certificate alone**,
  no package needed: the core carries the evidence that incriminates it.
- `core_hash_matches_core` — stored hash vs. recomputed hash of the stored core.
- `package_reproduces_core` — re-runs the kernel on the original package and
  requires byte-identical core (true logical replay; catches any field tamper).
- `signature_valid` — recorded as **non-critical**: a valid signature over a
  non-reproducing core must still fail overall. That inversion is the point.

**`redteam.py`** — the laundering/forgery vectors from the design turned into
executable attacks, each asserting the defended outcome:

| Attack | Defense asserted |
|---|---|
| A1 self-certification | → `Self-Attested Only`, never `Verified` |
| A2 inconclusive appended to a fail | → `Refuted with Evidentiary Gaps` |
| A3 ungrounded "pass" reading | span_grounding fails → stays `Refuted` |
| A4 uncertified pass vs certified fail | issued `Refuted`; boundary only **disclosed** as projected |
| A5 forged signed core | signature valid **and** conformance fails |
| A6 honest certificate | reproduces bit-for-bit |

## Recommended wiring (12-line CLI patch, your call)

Add a `verify-reproduction` subcommand so a third party can run the check without
writing Python:

```python
def _cmd_verify_reproduction(args):
    from .conformance import verify_certificate_conformance
    from .io import load_data, load_claim_package
    cert = load_data(args.certificate)
    pkg = load_claim_package(args.package) if args.package else None
    pub = load_public_key(args.public_key) if args.public_key else None
    report = verify_certificate_conformance(cert, package_data=pkg, public_key=pub)
    print(report.render())
    return 0 if report.ok else 1
```

## Doctrine recommendation

Make the meaning of a signature explicit in `SIGNING.md`: a ClaimBench signature
asserts *"I ran the kernel and obtained this core."* Verifiers MUST reproduce
before trusting. Signature = trust; reproduction = verification. Consider having
`verify-certificate` refuse to report PASS unless self-consistency also holds, so
the weak check can't be mistaken for the strong one.

## Not addressed here (next gaps, by priority)

1. **Pre-installed ambiguity** — an author grounding two verdict-straddling
   readings in the frozen record produces a *legitimate* Semantic Boundary by the
   gates, yet is engineered. Needs the co-location disclosure (ambiguity
   concentrated at the verdict-determining primitive), reported as structure, not
   alleged as intent. Requires richer primitive-level claim modeling than v2 has.
2. **Adjudication provenance is still asserted** — `claimbench_adjudicated` is a
   trusted label; nothing binds it to an actual adjudication artifact. A signed
   adjudication record per gate would let conformance check *that* too.
3. **Environmental replay** — `package_reproduces_core` is logical replay (same
   kernel version). Cross-version replay needs the kernel version pinned into a
   reproduction manifest.
