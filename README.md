# Earnings Surprise

**Quand une entreprise annonce des bénéfices meilleurs (ou pires) que prévu, comment réagit son action en bourse ?**

Ce projet compare, résultat par résultat :

- le **bénéfice par action (BPA) prévu** par les analystes,
- le **BPA réellement publié**,
- la **surprise** en % (écart entre les deux),
- la **réaction de l'action** à la première séance qui suit l'annonce.

Une bonne surprise fait-elle vraiment monter l'action ? Pas toujours : les marchés anticipent souvent, et d'autres éléments (chiffre d'affaires, prévisions de la direction) pèsent aussi.

## Exemple

```
$ python main.py AMZN

AMZN — 8 derniers résultats

                   Moment  BPA prévu  BPA réel  Surprise (%)  Réaction (%)
Date
2026-07-30  après clôture       1.83      5.75        214.89         15.32
2026-04-29  après clôture       1.65      2.78         68.18          0.77
2026-02-05  après clôture       1.95      1.95          0.22         -5.55
2025-10-30  après clôture       1.56      1.95         25.20          9.58
2025-07-31  après clôture       1.32      1.68         27.19         -8.27
...

Bonnes surprises : 8/8, dont 4 suivies d'une hausse de l'action.
```

## Comment la réaction est calculée

- Annonce **avant l'ouverture** : clôture du jour de l'annonce vs clôture de la veille.
- Annonce **après la clôture** (ou heure inconnue) : clôture du lendemain vs clôture du jour de l'annonce.

Les cours sont ajustés des dividendes et divisions d'actions.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py          # Amazon par défaut
python main.py AAPL     # ou n'importe quel ticker Yahoo Finance
```

## Feuille de route

1. ✅ Une seule action : les 8 derniers résultats
2. Plusieurs actions (Apple, LVMH, TotalEnergies…) : une bonne surprise fait-elle monter l'action ?
3. Graphique : nuage de points surprise vs réaction
4. Application web Streamlit : on tape un ticker, l'analyse s'affiche
5. Bonus : comparer les BPA GAAP et normalisés (non-GAAP), via le paramètre `methodology` ajouté à yfinance

## Données

Données issues de Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance). Projet pédagogique, pas un conseil en investissement.
