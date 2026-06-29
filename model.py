from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .engine import _canonical_json

SCHEME = "ed25519"
SIGNED_CERT_SCHEMA = "claimbench.signed_certificate.v2.1"
SIGNED_CERT_SCHEMAS = {SIGNED_CERT_SCHEMA, "claimbench.signed_certificate.v2.0"}
SIGNED_PACKAGE_SCHEMA = "claimbench.signed_package.v2.1"
SIGNED_PACKAGE_SCHEMAS = {SIGNED_PACKAGE_SCHEMA, "claimbench.signed_package.v2.0"}


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    raw = Path(path).read_bytes()
    key = serialization.load_pem_private_key(raw, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Private key must be an Ed25519 private key.")
    return key


def load_public_key(path: str | Path) -> Ed25519PublicKey:
    raw = Path(path).read_bytes()
    key = serialization.load_pem_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Public key must be an Ed25519 public key.")
    return key


def write_keypair(out_dir: str | Path, issuer: str = "claimbench-local") -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path = out / "claimbench_ed25519_private.pem"
    public_path = out / "claimbench_ed25519_public.pem"
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    kid = public_key_id(public_key)
    manifest = {
        "schema": "claimbench.key_manifest.v2.0",
        "issuer": issuer,
        "scheme": SCHEME,
        "key_id": kid,
        "public_key_pem": public_pem.decode("utf-8"),
        "created_at": utc_now(),
        "private_key_path": str(private_path.name),
        "public_key_path": str(public_path.name),
    }
    (out / "key_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"private_key": str(private_path), "public_key": str(public_path), "key_id": kid, "manifest": str(out / "key_manifest.json")}


def public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()[:24]


def sign_bytes(private_key: Ed25519PrivateKey, payload: bytes) -> bytes:
    return private_key.sign(payload)


def verify_bytes(public_key: Ed25519PublicKey, payload: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, payload)
        return True
    except InvalidSignature:
        return False


def make_signature_envelope(
    payload: Dict[str, Any],
    private_key: Ed25519PrivateKey,
    issuer: str,
    signed_payload: str,
    key_id: str | None = None,
) -> Dict[str, Any]:
    canonical = _canonical_json(payload).encode("utf-8")
    signature = sign_bytes(private_key, canonical)
    public_key = private_key.public_key()
    return {
        "scheme": SCHEME,
        "key_id": key_id or public_key_id(public_key),
        "issuer": issuer,
        "signed_payload": signed_payload,
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "signed_at": utc_now(),
        "signature_b64": b64e(signature),
    }


def verify_signature_envelope(payload: Dict[str, Any], signature_envelope: Dict[str, Any], public_key: Ed25519PublicKey) -> Tuple[bool, str]:
    if signature_envelope.get("scheme") != SCHEME:
        return False, f"Unsupported signature scheme: {signature_envelope.get('scheme')}"
    canonical = _canonical_json(payload).encode("utf-8")
    expected_hash = hashlib.sha256(canonical).hexdigest()
    if signature_envelope.get("payload_sha256") != expected_hash:
        return False, "Payload hash mismatch."
    try:
        sig = b64d(str(signature_envelope.get("signature_b64", "")))
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Invalid base64 signature: {exc}"
    if not verify_bytes(public_key, canonical, sig):
        return False, "Invalid signature."
    return True, "Signature verified."


def sign_certificate_dict(certificate: Dict[str, Any], private_key: Ed25519PrivateKey, issuer: str) -> Dict[str, Any]:
    if "certificate_core" not in certificate:
        raise ValueError("Certificate must contain certificate_core.")
    core = certificate["certificate_core"]
    signature = make_signature_envelope(core, private_key, issuer=issuer, signed_payload="certificate_core")
    signed = dict(certificate)
    existing = list(signed.get("signatures", []))
    existing.append(signature)
    signed["schema"] = SIGNED_CERT_SCHEMA
    signed["signatures"] = existing
    return signed


def verify_certificate_dict(certificate: Dict[str, Any], public_key: Ed25519PublicKey) -> Tuple[bool, List[str]]:
    if "certificate_core" not in certificate:
        return False, ["Missing certificate_core."]
    signatures = certificate.get("signatures", [])
    if not signatures:
        return False, ["Missing signatures."]
    messages: List[str] = []
    ok_any = False
    for sig in signatures:
        if sig.get("signed_payload") != "certificate_core":
            messages.append("Skipped non-certificate_core signature.")
            continue
        ok, msg = verify_signature_envelope(certificate["certificate_core"], sig, public_key)
        messages.append(msg)
        ok_any = ok_any or ok
    return ok_any, messages


def sign_claim_package(package: Dict[str, Any], private_key: Ed25519PrivateKey, issuer: str) -> Dict[str, Any]:
    signature = make_signature_envelope(package, private_key, issuer=issuer, signed_payload="claim_package")
    return {"schema": SIGNED_PACKAGE_SCHEMA, "package": package, "signatures": [signature]}


def verify_claim_package_envelope(envelope: Dict[str, Any], public_key: Ed25519PublicKey) -> Tuple[bool, List[str]]:
    if envelope.get("schema") not in SIGNED_PACKAGE_SCHEMAS:
        return False, ["Not a ClaimBench signed package envelope."]
    if "package" not in envelope:
        return False, ["Missing package payload."]
    signatures = envelope.get("signatures", [])
    if not signatures:
        return False, ["Missing signatures."]
    messages: List[str] = []
    ok_any = False
    for sig in signatures:
        if sig.get("signed_payload") != "claim_package":
            messages.append("Skipped non-claim_package signature.")
            continue
        ok, msg = verify_signature_envelope(envelope["package"], sig, public_key)
        messages.append(msg)
        ok_any = ok_any or ok
    return ok_any, messages
