# RECU

A signed receipt. Not money.

This rail is a signed receipt. Not money. Not a quantum coin. FAMILLE attests. It does not hold funds.

Rails named only: `x-money | visa | interac | ach | cash | autre`.

X Money (2026, US Premium, Visa + Cross River FDIC) is a rail we can *name*. We cannot operate it. We cannot patch X.

Attestation ≠ balance. A sealed card is not a QUANTUM seal. Keys stay off Git.

## Verified vs assumed

| | Verified | Assumed |
| --- | --- | --- |
| Object | A local `recu.v0` card signed with ed25519 (`local-v0`) | That money moved, or that this file is money |
| Rail | The name is one of `x-money \| visa \| interac \| ach \| cash \| autre` | That Visa, Interac, ACH, cash, or X Money settled |
| X Money | We may write `rail: x-money` | That we operate X Money, that we can patch X, that X paid |
| Seal | `sceau.suite` is `ed25519` on the card body | A QUANTUM seal, UFHY1, or a mint |
| Keys | Generated under `keys/`, kept off Git | That FAMILLE holds a wallet or a balance |
| FAMILLE | Attests | Holds funds |
| Amount | `montant_cents > 0` on the card | A coin, a mint, or a spendable balance |

A valid seal means the receipt holds. If money moved, it moved elsewhere.

## How to run

Runtime (ed25519 only — not a quantum stack):

```
pip install cryptography
```

```
python3 recu.py cles
python3 recu.py ecrire --montant 25 --devise USD --rail x-money --de @alice --vers @bob --ref xm-demo
python3 recu.py sceller carte.recu.json
python3 recu.py juger carte.recu.json
```

- `cles` writes `keys/ed25519.sk` and `keys/ed25519.pk`. Note: `not QUANTUM. not a mint. keys off Git.`
- `ecrire` writes a card. `montant_cents <= 0` is refused. Zero is not a receipt. Unknown rail is denied.
- `sceller` signs the card body. Suite on the card is local ed25519 v0.
- `juger` denies an unsealed card (`pas de sceau`) and a broken seal. A valid seal is allowed. The note says money, if it moved, moved elsewhere.

Tests: `python3 -m unittest test_recu.py -v`

Ritual (meaning unchanged): [INTERDIT.md](INTERDIT.md) · [JUGE.md](JUGE.md)
