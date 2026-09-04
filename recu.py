#!/usr/bin/env python3
"""RECU v0 — a signed receipt. Not money."""
from __future__ import annotations
import argparse, hashlib, json, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
FORMAT = "recu.v0"
RAILS = ("x-money", "visa", "interac", "ach", "cash", "autre")
DEVISES = ("CAD", "USD")
MONEY_FIELDS = frozenset({"balance", "wallet", "mint", "solde"})
INVENTED_COIN = ("quantum coin", "quantum money")
CLES_NOTE = "not QUANTUM. not a mint. keys off Git."
ECRIRE_NOTE = "attestation, pas un solde. FAMILLE ne tient pas l'argent."
JUGER_NOTE = "le reçu tient. l'argent, s'il a bougé, a bougé ailleurs."


def _invented_coin(carte):
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in MONEY_FIELDS:
                    return True
                if walk(v):
                    return True
        elif isinstance(obj, str):
            low = obj.lower()
            if any(p in low for p in INVENTED_COIN):
                return True
        elif isinstance(obj, (list, tuple)):
            return any(walk(x) for x in obj)
        return False
    return walk(carte)


def _refuse_invented_text(*parts):
    blob = " ".join(str(p) for p in parts if p).lower()
    if any(p in blob for p in INVENTED_COIN):
        raise SystemExit("refus : pas de monnaie inventée")

def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _payload(carte):
    corps = {k: v for k, v in carte.items() if k != "sceau"}
    return json.dumps(corps, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def keys_dir(root="keys"):
    d = Path(root).expanduser(); d.mkdir(parents=True, exist_ok=True); return d

def cles(root="keys"):
    d = keys_dir(root)
    sk = ed25519.Ed25519PrivateKey.generate()
    (d / "ed25519.sk").write_bytes(sk.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    (d / "ed25519.pk").write_bytes(sk.public_key().public_bytes_raw())
    return {"signer": "local-v0", "suite": "ed25519", "note": CLES_NOTE, "pk_sha256": hashlib.sha256(sk.public_key().public_bytes_raw()).hexdigest()}

def ecrire(montant, devise, rail, de_, vers, ref=None):
    rail = (rail or "").strip().lower(); devise = (devise or "CAD").strip().upper()
    if rail not in RAILS: raise SystemExit("rail : x-money | visa | interac | ach | cash | autre")
    if devise not in DEVISES: raise SystemExit("devise : CAD | USD")
    _refuse_invented_text(de_, vers, ref)
    try: cents = int(round(float(montant) * 100))
    except ValueError as e: raise SystemExit("montant : nombre") from e
    if cents <= 0: raise SystemExit("refus : un reçu n'atteste pas zéro")
    return {"format": FORMAT, "recu_id": "RC-" + uuid.uuid4().hex[:12], "montant_cents": cents, "devise": devise, "rail": rail, "de": de_, "vers": vers, "ref_externe": ref, "suite": "ed25519", "pose_at": _now(), "sceau": None, "note": ECRIRE_NOTE}

def sceller(carte, root="keys"):
    sk = ed25519.Ed25519PrivateKey.from_private_bytes((keys_dir(root) / "ed25519.sk").read_bytes())
    msg = _payload(carte); sig = sk.sign(msg)
    carte["sceau"] = {"suite": "ed25519", "signer": "local-v0", "pk_hex": sk.public_key().public_bytes_raw().hex(), "sig_hex": sig.hex(), "message_sha256": hashlib.sha256(msg).hexdigest()}
    return carte

def juger(carte):
    if carte.get("format") != FORMAT: return {"decision": "deny", "reason": "pas un recu.v0"}
    if carte.get("rail") not in RAILS: return {"decision": "deny", "reason": "rail inconnu"}
    if int(carte.get("montant_cents") or 0) <= 0: return {"decision": "deny", "reason": "montant"}
    if _invented_coin(carte): return {"decision": "deny", "reason": "pas de monnaie inventée"}
    if carte.get("suite") != "ed25519": return {"decision": "deny", "reason": "suite"}
    sceau = carte.get("sceau")
    if not sceau: return {"decision": "deny", "reason": "pas de sceau", "flag": "recu"}
    if sceau.get("suite") != "ed25519": return {"decision": "deny", "reason": "sceau:suite"}
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(sceau["pk_hex"])).verify(bytes.fromhex(sceau["sig_hex"]), _payload(carte))
    except Exception as e:
        return {"decision": "deny", "reason": "sceau:" + type(e).__name__}
    return {"decision": "allow", "flag": "recu", "rail": carte["rail"], "montant_cents": carte["montant_cents"], "devise": carte["devise"], "note": JUGER_NOTE}

def main(argv=None):
    p = argparse.ArgumentParser(prog="recu"); sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cles").add_argument("--keys", default="keys")
    pe = sub.add_parser("ecrire")
    pe.add_argument("--montant", required=True); pe.add_argument("--devise", default="CAD"); pe.add_argument("--rail", required=True)
    pe.add_argument("--de", required=True); pe.add_argument("--vers", required=True); pe.add_argument("--ref", default=None); pe.add_argument("--out", default="carte.recu.json")
    ps = sub.add_parser("sceller"); ps.add_argument("fichier"); ps.add_argument("--keys", default="keys")
    pj = sub.add_parser("juger"); pj.add_argument("fichier")
    args = p.parse_args(argv)
    if args.cmd == "cles":
        print(json.dumps(cles(args.keys), ensure_ascii=False, indent=2))
    elif args.cmd == "ecrire":
        carte = ecrire(args.montant, args.devise, args.rail, args.de, args.vers, args.ref)
        Path(args.out).write_text(json.dumps(carte, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(carte, ensure_ascii=False, indent=2))
    elif args.cmd == "sceller":
        carte = sceller(json.loads(Path(args.fichier).read_text()), args.keys)
        Path(args.fichier).write_text(json.dumps(carte, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(carte, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(juger(json.loads(Path(args.fichier).read_text())), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
