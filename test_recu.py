#!/usr/bin/env python3
"""Locks for RECU v0 — a signed receipt. Not money."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import recu

ROOT = Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
RECUPY = (ROOT / "recu.py").read_text(encoding="utf-8")
MONEY_FIELDS = ("balance", "wallet", "mint")
INVENTED = ("quantum coin", "quantum money")
NAMED_RAILS = ("x-money", "visa", "interac", "ach", "cash", "autre")


def _card(**overrides):
    carte = recu.ecrire(25, "USD", "x-money", "@alice", "@bob", "xm-demo")
    carte.update(overrides)
    return carte


def _seal(carte, keys):
    return recu.sceller(carte, root=keys)


class DoorCopy(unittest.TestCase):
    def test_lead_signed_receipt_not_money(self):
        self.assertIn("A signed receipt. Not money.", README)

    def test_named_rails_only(self):
        self.assertIn("x-money | visa | interac | ach | cash | autre", README)

    def test_x_money_named_not_operated(self):
        self.assertIn("X Money (2026, US Premium, Visa + Cross River FDIC)", README)
        self.assertIn("We cannot operate it.", README)
        self.assertIn("We cannot patch X.", README)

    def test_attestation_not_balance(self):
        self.assertIn("Attestation ≠ balance", README)
        self.assertIn("A sealed card is not a QUANTUM seal", README)
        self.assertIn("Keys stay off Git", README)

    def test_verified_vs_assumed_table(self):
        self.assertIn("Verified vs assumed", README)
        self.assertIn("| Verified |", README)
        self.assertIn("| Assumed |", README)

    def test_how_to_run_cli(self):
        for line in (
            "python3 recu.py cles",
            "python3 recu.py ecrire",
            "python3 recu.py sceller",
            "python3 recu.py juger",
            "pip install cryptography",
        ):
            self.assertIn(line, README)

    def test_famille_does_not_hold_funds(self):
        self.assertIn("It does not hold funds", README)
        self.assertIn("FAMILLE attests", README)

    def test_no_formally_verified(self):
        self.assertNotIn("formally verified", README.lower())
        self.assertNotIn("formally verified", RECUPY.lower())

    def test_no_grok_imagine(self):
        blob = (README + RECUPY).lower()
        self.assertNotIn("grok imagine", blob)

    def test_no_license_file_added(self):
        self.assertFalse((ROOT / "LICENSE").exists())


class Lock1ReceiptIsNotMoney(unittest.TestCase):
    def test_json_has_no_balance_wallet_mint(self):
        carte = _card()
        keys = {k.lower() for k in carte}
        for field in MONEY_FIELDS:
            self.assertNotIn(field, keys)
        blob = json.dumps(carte, ensure_ascii=False)
        for field in MONEY_FIELDS:
            self.assertNotIn(f'"{field}"', blob)

    def test_juger_denies_balance_wallet_mint_fields(self):
        for field in MONEY_FIELDS:
            with self.subTest(field=field):
                carte = _card()
                carte[field] = 1
                out = recu.juger(carte)
                self.assertEqual(out["decision"], "deny")
                self.assertEqual(out["reason"], "pas de monnaie inventée")


class Lock2NoQuantumCoin(unittest.TestCase):
    def test_generated_json_refuses_invented_coin(self):
        carte = _card()
        blob = json.dumps(carte, ensure_ascii=False).lower()
        for phrase in INVENTED:
            self.assertNotIn(phrase, blob)
        self.assertNotIn("coin", json.dumps(list(carte.keys())))

    def test_ecrire_refuses_quantum_coin_copy(self):
        with self.assertRaises(SystemExit) as ctx:
            recu.ecrire(25, "USD", "x-money", "@alice", "quantum coin", "xm")
        self.assertIn("monnaie inventée", str(ctx.exception))

    def test_juger_denies_quantum_money_on_card(self):
        carte = _card(note="this is quantum money")
        out = recu.juger(carte)
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(out["reason"], "pas de monnaie inventée")

    def test_copy_does_not_invent_a_coin(self):
        for phrase in INVENTED:
            for source, text in (("README", README), ("recu.py", RECUPY)):
                if phrase in text.lower():
                    idx = text.lower().index(phrase)
                    window = text[max(0, idx - 24) : idx].lower()
                    self.assertTrue(
                        any(tok in window for tok in ("not ", "no ", "pas ", "≠", "refuse")),
                        f"{source} invents {phrase}",
                    )


class Lock3QuantumOffTheCardAsSeal(unittest.TestCase):
    def test_cles_note_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = recu.cles(tmp)
        self.assertEqual(out["note"], "not QUANTUM. not a mint. keys off Git.")
        self.assertEqual(out["suite"], "ed25519")
        self.assertEqual(out["signer"], "local-v0")

    def test_sceau_suite_is_not_quantum(self):
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sealed = _seal(_card(), tmp)
        self.assertEqual(sealed["sceau"]["suite"], "ed25519")
        self.assertNotEqual(sealed["sceau"]["suite"].upper(), "QUANTUM")


class Lock4NamedRailsOnly(unittest.TestCase):
    def test_named_rails_write(self):
        for rail in NAMED_RAILS:
            carte = recu.ecrire(1, "CAD", rail, "@a", "@b")
            self.assertEqual(carte["rail"], rail)

    def test_unknown_rail_ecrire_denies(self):
        with self.assertRaises(SystemExit) as ctx:
            recu.ecrire(25, "USD", "bitcoin", "@a", "@b")
        self.assertIn("x-money | visa | interac | ach | cash | autre", str(ctx.exception))

    def test_unknown_rail_juger_denies(self):
        out = recu.juger(_card(rail="swift"))
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(out["reason"], "rail inconnu")


class Lock5ZeroNegativeRefuse(unittest.TestCase):
    def test_zero_ecrire(self):
        with self.assertRaises(SystemExit) as ctx:
            recu.ecrire(0, "USD", "cash", "@a", "@b")
        self.assertIn("zéro", str(ctx.exception))

    def test_negative_ecrire(self):
        with self.assertRaises(SystemExit):
            recu.ecrire(-5, "USD", "cash", "@a", "@b")

    def test_zero_cents_juger(self):
        out = recu.juger(_card(montant_cents=0))
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(out["reason"], "montant")

    def test_negative_cents_juger(self):
        out = recu.juger(_card(montant_cents=-1))
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(out["reason"], "montant")


class Lock6SealRequired(unittest.TestCase):
    def test_unsealed_deny(self):
        out = recu.juger(_card())
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(out["reason"], "pas de sceau")

    def test_seal_verify_fail_deny(self):
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sealed = _seal(_card(), tmp)
        sealed["sceau"]["sig_hex"] = "00" * 64
        out = recu.juger(sealed)
        self.assertEqual(out["decision"], "deny")
        self.assertTrue(out["reason"].startswith("sceau:"))

    def test_valid_seal_allow_and_money_moved_elsewhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sealed = _seal(_card(), tmp)
            out = recu.juger(sealed)
        self.assertEqual(out["decision"], "allow")
        self.assertIn("ailleurs", out["note"])
        self.assertIn("bougé", out["note"])


class Lock7FamilleDoesNotHoldFunds(unittest.TestCase):
    def test_door_and_ecrire_note(self):
        self.assertIn("does not hold funds", README)
        carte = _card()
        self.assertIn("FAMILLE ne tient pas l'argent", carte["note"])
        self.assertIn("attestation, pas un solde", carte["note"])


class Lock8NameXMoneyDoNotOperate(unittest.TestCase):
    def test_x_money_is_a_named_rail(self):
        self.assertIn("x-money", recu.RAILS)
        carte = recu.ecrire(10, "USD", "x-money", "@a", "@b", "xm-demo")
        self.assertEqual(carte["rail"], "x-money")

    def test_door_does_not_claim_to_operate_or_patch_x(self):
        self.assertIn("We cannot operate it.", README)
        self.assertIn("We cannot patch X.", README)
        self.assertNotIn("we operate X", README.lower())
        self.assertNotIn("patch X Money", README)


class Lock9KeysOffGit(unittest.TestCase):
    def test_gitignore_covers_keys_if_present(self):
        gi = ROOT / ".gitignore"
        if not gi.exists():
            self.skipTest("no .gitignore")
        text = gi.read_text(encoding="utf-8")
        self.assertIn("keys/", text)
        self.assertIn("*.sk", text)
        self.assertIn("*.pk", text)

    def test_generated_keys_are_ignored(self):
        gi = ROOT / ".gitignore"
        if not gi.exists():
            self.skipTest("no .gitignore")
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sk = Path(tmp) / "ed25519.sk"
            pk = Path(tmp) / "ed25519.pk"
            self.assertTrue(sk.exists())
            self.assertTrue(pk.exists())
        tracked = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files", "keys", "*.sk", "*.pk"],
            text=True,
        ).strip()
        self.assertEqual(tracked, "")

    def test_check_ignore_keys_dir(self):
        gi = ROOT / ".gitignore"
        if not gi.exists():
            self.skipTest("no .gitignore")
        out = subprocess.check_output(
            ["git", "-C", str(ROOT), "check-ignore", "-v", "keys/ed25519.sk"],
            text=True,
        )
        self.assertIn("keys/", out)


class Lock10LocalEd25519NotUfhy1(unittest.TestCase):
    def test_suite_on_card_is_local_ed25519(self):
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sealed = _seal(_card(), tmp)
        self.assertEqual(sealed["suite"], "ed25519")
        self.assertEqual(sealed["sceau"]["suite"], "ed25519")
        self.assertEqual(sealed["sceau"]["signer"], "local-v0")
        blob = json.dumps(sealed)
        self.assertNotIn("UFHY1", blob)
        self.assertNotEqual(sealed["sceau"]["suite"].upper(), "QUANTUM")

    def test_ufhy1_and_quantum_suite_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            recu.cles(tmp)
            sealed = _seal(_card(), tmp)
        sealed["sceau"]["suite"] = "UFHY1"
        out = recu.juger(sealed)
        self.assertEqual(out["decision"], "deny")
        sealed["sceau"]["suite"] = "QUANTUM"
        out = recu.juger(sealed)
        self.assertEqual(out["decision"], "deny")

    def test_no_quantum_stack_import(self):
        self.assertIn("from cryptography.hazmat.primitives.asymmetric import ed25519", RECUPY)
        self.assertNotIn("ufhy", RECUPY.lower())


class CliEntrypoints(unittest.TestCase):
    def test_cli_cles_ecrire_sceller_juger(self):
        with tempfile.TemporaryDirectory() as tmp:
            keys = Path(tmp) / "keys"
            carte = Path(tmp) / "carte.recu.json"
            cles = subprocess.run(
                ["python3", str(ROOT / "recu.py"), "cles", "--keys", str(keys)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("not QUANTUM. not a mint. keys off Git.", cles.stdout)
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "recu.py"),
                    "ecrire",
                    "--montant",
                    "25",
                    "--devise",
                    "USD",
                    "--rail",
                    "x-money",
                    "--de",
                    "@alice",
                    "--vers",
                    "@bob",
                    "--ref",
                    "xm-demo",
                    "--out",
                    str(carte),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            unsealed = json.loads(carte.read_text())
            self.assertIsNone(unsealed["sceau"])
            judge_open = subprocess.run(
                ["python3", str(ROOT / "recu.py"), "juger", str(carte)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("pas de sceau", judge_open.stdout)
            subprocess.run(
                ["python3", str(ROOT / "recu.py"), "sceller", str(carte), "--keys", str(keys)],
                check=True,
                capture_output=True,
                text=True,
            )
            judge_ok = subprocess.run(
                ["python3", str(ROOT / "recu.py"), "juger", str(carte)],
                check=True,
                capture_output=True,
                text=True,
            )
            verdict = json.loads(judge_ok.stdout)
            self.assertEqual(verdict["decision"], "allow")
            self.assertIn("ailleurs", verdict["note"])


if __name__ == "__main__":
    unittest.main()
