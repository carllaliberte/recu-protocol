# RECU

Un reçu signé. Pas d'argent.

Ce rail est un reçu signé. Pas d'argent. Pas de quantum coin. FAMILLE atteste. Elle ne tient pas les fonds.

Rails nommés seulement : `x-money | visa | interac | ach | cash | autre`.

X Money (2026, US Premium, Visa + Cross River FDIC) est un rail qu'on peut *nommer*. On ne l'opère pas. On ne patche pas X.

Attestation ≠ solde. Une carte scellée n'est pas un sceau QUANTUM. Les clés restent hors Git.

## Vérifié vs présumé

| | Vérifié | Présumé |
| --- | --- | --- |
| Objet | Une carte locale `recu.v0` signée avec ed25519 (`local-v0`) | Que l'argent a bougé, ou que ce fichier est de l'argent |
| Rail | Le nom est l'un de `x-money \| visa \| interac \| ach \| cash \| autre` | Que Visa, Interac, ACH, cash ou X Money a réglé |
| X Money | On peut écrire `rail: x-money` | Qu'on opère X Money, qu'on peut patcher X, que X a payé |
| Sceau | `sceau.suite` est `ed25519` sur le corps de la carte | Un sceau QUANTUM, UFHY1, ou un mint |
| Clés | Générées sous `keys/`, tenues hors Git | Que FAMILLE tient un wallet ou un solde |
| FAMILLE | Atteste | Tient les fonds |
| Montant | `montant_cents > 0` sur la carte | Une pièce, un mint, ou un solde dépensable |

Un sceau valide veut dire que le reçu tient. Si l'argent a bougé, il a bougé ailleurs.

## Comment lancer

Runtime (ed25519 seulement — pas une pile quantique) :

```
pip install cryptography
```

```
python3 recu.py cles
python3 recu.py ecrire --montant 25 --devise USD --rail x-money --de @alice --vers @bob --ref xm-demo
python3 recu.py sceller carte.recu.json
python3 recu.py juger carte.recu.json
```

- `cles` écrit `keys/ed25519.sk` et `keys/ed25519.pk`. Note : `not QUANTUM. not a mint. keys off Git.`
- `ecrire` écrit une carte. `montant_cents <= 0` est refusé. Zéro n'est pas un reçu. Rail inconnu : deny.
- `sceller` signe le corps de la carte. Suite sur la carte : ed25519 v0 local.
- `juger` refuse une carte non scellée (`pas de sceau`) et un sceau brisé. Un sceau valide : allow. La note dit que l'argent, s'il a bougé, a bougé ailleurs.

Tests : `python3 -m unittest test_recu.py -v`

Rituel (sens inchangé) : [INTERDIT.md](INTERDIT.md) · [JUGE.md](JUGE.md)
