from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .conformance import verify_certificate_conformance
from .crypto import (
    load_private_key,
    load_public_key,
    sign_certificate_dict,
    sign_claim_package,
    verify_certificate_dict,
    verify_claim_package_envelope,
    write_keypair,
)
from .engine import evaluate_claim_package
from .formalizer import formalize_brief, provider_from_args
from .io import load_claim_package, load_data, write_data, write_json, write_text
from .report import render_markdown_certificate
from .validators import validate_claim_package


def _cmd_validate(args: argparse.Namespace) -> int:
    data = load_claim_package(args.package)
    errors = validate_claim_package(data)
    if errors:
        print("Invalid ClaimBench package:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Valid ClaimBench package.")
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    data = load_claim_package(args.package)
    errors = validate_claim_package(data)
    if errors and not args.force:
        print("Invalid ClaimBench package. Use --force to evaluate anyway.")
        for err in errors:
            print(f"  - {err}")
        return 1

    result = evaluate_claim_package(data)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.package).stem
    cert_dict = result.to_dict()

    if args.sign_private_key:
        private_key = load_private_key(args.sign_private_key)
        cert_dict = sign_certificate_dict(cert_dict, private_key, issuer=args.issuer)

    if args.format in {"json", "both"}:
        write_json(out_dir / f"{stem}.certificate.json", cert_dict)
    if args.format in {"markdown", "both"}:
        write_text(out_dir / f"{stem}.certificate.md", render_markdown_certificate(result, signed=bool(args.sign_private_key)))

    print(f"Badge: {result.badge.value}")
    print(f"Rationale: {result.rationale}")
    print(f"Core hash: {result.core_hash()}")
    if args.sign_private_key:
        print(f"Signature: added Ed25519 certificate_core signature by {args.issuer}")
    if result.projected_badge and result.projected_badge != result.badge:
        print(f"Assertion-contingent badge: {result.projected_badge.value}")
    print(f"Certified admitted: {', '.join(result.admitted_formalizations) or '-'}")
    print(f"Asserted admitted: {', '.join(result.asserted_admitted_formalizations) or '-'}")
    print(f"Uncertified: {', '.join(result.uncertified_formalizations) or '-'}")
    print(f"Rejected: {', '.join(result.rejected_formalizations) or '-'}")
    print(f"Reports written to: {out_dir}")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path)
    target.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parents[2]
    examples_src = here / "examples"
    docs_src = here / "docs"
    schema_src = here / "schema"
    for src, name in [(examples_src, "examples"), (docs_src, "docs"), (schema_src, "schema")]:
        dest = target / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    for fname in ["STANDARD.md", "README.md"]:
        shutil.copy2(here / fname, target / fname)
    print(f"Initialized ClaimBench workspace at {target}")
    return 0


def _cmd_keygen(args: argparse.Namespace) -> int:
    info = write_keypair(args.out, issuer=args.issuer)
    print(f"Generated Ed25519 keypair in {args.out}")
    print(f"Key ID: {info['key_id']}")
    print(f"Private key: {info['private_key']}")
    print(f"Public key: {info['public_key']}")
    print(f"Manifest: {info['manifest']}")
    return 0


def _cmd_sign_certificate(args: argparse.Namespace) -> int:
    cert = load_data(args.certificate)
    private_key = load_private_key(args.private_key)
    signed = sign_certificate_dict(cert, private_key, issuer=args.issuer)
    out = Path(args.out) if args.out else Path(args.certificate).with_suffix(".signed.json")
    write_json(out, signed)
    print(f"Signed certificate written to: {out}")
    print(f"Signature count: {len(signed.get('signatures', []))}")
    return 0


def _cmd_verify_certificate(args: argparse.Namespace) -> int:
    cert = load_data(args.certificate)
    public_key = load_public_key(args.public_key)
    sig_ok, messages = verify_certificate_dict(cert, public_key)
    conformance = verify_certificate_conformance(cert, package_data=None, public_key=public_key)
    ok = sig_ok and conformance.ok
    print("Certificate verification:", "PASS" if ok else "FAIL")
    print("Signature:", "PASS" if sig_ok else "FAIL")
    for msg in messages:
        print(f"  - {msg}")
    print(conformance.render())
    return 0 if ok else 1


def _cmd_verify_reproduction(args: argparse.Namespace) -> int:
    cert = load_data(args.certificate)
    package = load_claim_package(args.package) if args.package else None
    public_key = load_public_key(args.public_key) if args.public_key else None
    report = verify_certificate_conformance(cert, package_data=package, public_key=public_key)
    print(report.render())
    return 0 if report.ok else 1


def _cmd_sign_package(args: argparse.Namespace) -> int:
    package = load_claim_package(args.package)
    private_key = load_private_key(args.private_key)
    signed = sign_claim_package(package, private_key, issuer=args.issuer)
    out = Path(args.out) if args.out else Path(args.package).with_suffix(".signed.json")
    write_json(out, signed)
    print(f"Signed package written to: {out}")
    return 0


def _cmd_verify_package(args: argparse.Namespace) -> int:
    envelope = load_data(args.package)
    public_key = load_public_key(args.public_key)
    ok, messages = verify_claim_package_envelope(envelope, public_key)
    print("Package verification:", "PASS" if ok else "FAIL")
    for msg in messages:
        print(f"  - {msg}")
    return 0 if ok else 1


def _cmd_formalize(args: argparse.Namespace) -> int:
    brief = load_data(args.brief)
    provider = provider_from_args(args.provider, command=args.command, endpoint=args.endpoint, token=args.token)
    package = formalize_brief(brief, provider)
    out = Path(args.out)
    write_data(out, package)
    print(f"Formalized package written to: {out}")
    print(f"Provider: {args.provider}")
    print("Note: generated gates are llm_proposed and do not support a certified badge until adjudicated.")
    if args.evaluate:
        result = evaluate_claim_package(package)
        print(f"Projected evaluation badge: {result.badge.value}")
        print(f"Projected rationale: {result.rationale}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claimbench", description="ClaimBench signed claim certificate CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate a ClaimBench package")
    p_validate.add_argument("package")
    p_validate.set_defaults(func=_cmd_validate)

    p_eval = sub.add_parser("evaluate", help="Evaluate a ClaimBench package and emit a certificate")
    p_eval.add_argument("package")
    p_eval.add_argument("--out", default="reports", help="Output directory")
    p_eval.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    p_eval.add_argument("--force", action="store_true", help="Evaluate even when validation reports errors")
    p_eval.add_argument("--sign-private-key", help="Optional Ed25519 private key PEM used to sign the certificate core")
    p_eval.add_argument("--issuer", default="claimbench-local", help="Signature issuer name")
    p_eval.set_defaults(func=_cmd_evaluate)

    p_init = sub.add_parser("init", help="Initialize a starter ClaimBench workspace")
    p_init.add_argument("path")
    p_init.set_defaults(func=_cmd_init)

    p_keygen = sub.add_parser("keygen", help="Generate an Ed25519 signing keypair")
    p_keygen.add_argument("--out", default="keys", help="Output directory for generated keys")
    p_keygen.add_argument("--issuer", default="claimbench-local")
    p_keygen.set_defaults(func=_cmd_keygen)

    p_sign_cert = sub.add_parser("sign-certificate", help="Sign an existing certificate JSON")
    p_sign_cert.add_argument("certificate")
    p_sign_cert.add_argument("--private-key", required=True)
    p_sign_cert.add_argument("--issuer", default="claimbench-local")
    p_sign_cert.add_argument("--out")
    p_sign_cert.set_defaults(func=_cmd_sign_certificate)

    p_verify_cert = sub.add_parser("verify-certificate", help="Verify a signed certificate JSON and check core self-consistency")
    p_verify_cert.add_argument("certificate")
    p_verify_cert.add_argument("--public-key", required=True)
    p_verify_cert.set_defaults(func=_cmd_verify_certificate)

    p_verify_repro = sub.add_parser("verify-reproduction", help="Verify certificate self-consistency and optionally reproduce it from the source package")
    p_verify_repro.add_argument("certificate")
    p_verify_repro.add_argument("--package", help="Original claim package or signed package envelope used to produce the certificate")
    p_verify_repro.add_argument("--public-key", help="Optional Ed25519 public key PEM to record signature validity")
    p_verify_repro.set_defaults(func=_cmd_verify_reproduction)

    p_sign_pkg = sub.add_parser("sign-package", help="Sign a claim package into a signed package envelope")
    p_sign_pkg.add_argument("package")
    p_sign_pkg.add_argument("--private-key", required=True)
    p_sign_pkg.add_argument("--issuer", default="claimbench-local")
    p_sign_pkg.add_argument("--out")
    p_sign_pkg.set_defaults(func=_cmd_sign_package)

    p_verify_pkg = sub.add_parser("verify-package", help="Verify a signed package envelope")
    p_verify_pkg.add_argument("package")
    p_verify_pkg.add_argument("--public-key", required=True)
    p_verify_pkg.set_defaults(func=_cmd_verify_package)

    p_formalize = sub.add_parser("formalize", help="Generate a draft ClaimBench package from a formalizer brief")
    p_formalize.add_argument("brief")
    p_formalize.add_argument("--provider", choices=["mock", "command", "http-json"], default="mock")
    p_formalize.add_argument("--command", help="Command provider: executable receiving brief JSON on stdin")
    p_formalize.add_argument("--endpoint", help="HTTP JSON provider endpoint")
    p_formalize.add_argument("--token", help="Optional bearer token for HTTP JSON provider")
    p_formalize.add_argument("--out", required=True, help="Output .yaml/.yml/.json package path")
    p_formalize.add_argument("--evaluate", action="store_true", help="Immediately run the badge engine on the generated draft")
    p_formalize.set_defaults(func=_cmd_formalize)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
