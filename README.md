# RECU

A signed receipt. Not money.

Rail named: `x-money | visa | interac | ach | cash | autre`.
FAMILLE attests. It does not hold funds.

X Money (2026, US Premium, Visa + Cross River FDIC) is a rail we can *name*. We cannot operate it. We cannot patch X.

```
python3 recu.py cles
python3 recu.py ecrire --montant 25 --devise USD --rail x-money --de @alice --vers @bob --ref xm-demo
python3 recu.py sceller carte.recu.json
python3 recu.py juger carte.recu.json
```
