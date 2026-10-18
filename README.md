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

## Plusieurs actions

`python multi.py` applique l'analyse à **54 grandes entreprises** (35 américaines, 19 européennes dont 11 du CAC 40), soit **432 résultats trimestriels**, puis `python scatter.py` trace le nuage de points :

![Surprise de BPA vs réaction de l'action](scatter.png)

Ce qui en ressort :

- **Une mauvaise surprise est punie** : baisse dans 69 % des cas, −2,3 % en moyenne.
- **Une bonne surprise n'est guère récompensée** : hausse dans 53 % des cas seulement, à peine mieux qu'à pile ou face, pour +0,2 % en moyenne. Battre le consensus est déjà attendu par le marché.
- **Il faut une très grosse surprise pour faire bouger l'action** : la réaction moyenne reste sous +0,5 % jusqu'à 20 % de surprise, et n'atteint que +1,6 % au-delà.
- La corrélation (de rangs) entre surprise et réaction est faible (+0,20), et varie beaucoup d'une entreprise à l'autre : très forte pour Bank of America ou Allianz (+0,95), négative pour Adobe (−0,60) ou ExxonMobil (−0,57).

**Pourquoi seulement 11 valeurs du CAC 40 ?** Yahoo Finance n'a pas d'historique trimestriel de BPA prévu/réel pour la plupart des autres (LVMH, L'Oréal, Hermès, Safran, Schneider…), souvent parce qu'elles ne publient leurs bénéfices que deux fois par an. Elles sont donc absentes de l'échantillon.

## Comment la réaction est calculée

- Annonce **avant l'ouverture** : clôture du jour de l'annonce vs clôture de la veille.
- Annonce **après la clôture** : clôture du lendemain vs clôture du jour de l'annonce.
- **Heure incertaine** (Yahoo indique une heure en pleine séance, souvent approximative pour les valeurs européennes) : clôture du lendemain vs clôture de la veille.

Yahoo donne les heures d'annonce en heure de New York ; elles sont converties dans le fuseau de la place de cotation (Paris, Londres, Francfort, Copenhague…), dont on utilise les horaires d'ouverture et de clôture.

Les cours sont ajustés des dividendes et divisions d'actions.

## Application web

```bash
streamlit run app.py
```

On tape le nom d'une entreprise (« Amazon », « Airbus », « TotalEnergies »…) ou un ticker, on choisit la cotation, et l'analyse s'affiche : tableau des derniers résultats, nuage de points, comparaison GAAP / normalisé. Un second onglet reprend l'analyse des 54 entreprises.

## Bonus : BPA GAAP ou normalisé ?

Le BPA **GAAP** est le chiffre comptable, éléments exceptionnels compris (plus-values sur participations, dépréciations, restructurations). Le BPA **normalisé** (non-GAAP) les retire. Les deux surprises peuvent raconter des histoires opposées :

| Trimestre | Surprise GAAP | Surprise normalisée | Réaction |
|---|---|---|---|
| Amazon, T2 2026 | +214,9 % | +7,3 % | +15,3 % |
| Amazon, T1 2026 | +68,2 % | −2,2 % | +0,8 % |
| Alphabet, T2 2026 | +214,2 % | −2,2 % | −7,1 % |
| Sanofi, T4 2025 | −173,2 % | +4,4 % | −0,6 % |

`python gaap.py` compare les deux sur les 4 derniers trimestres des 54 entreprises (208 résultats ; Bouygues n'a pas de données GAAP/normalisé). Les deux surprises diffèrent de plus de 10 points dans 79 cas et sont **de signe opposé dans 71 cas**, soit un tiers des résultats. La surprise normalisée suit un peu mieux la bourse :

| | Corrélation (rangs) avec la réaction | Même sens que la bourse |
|---|---|---|
| GAAP | +0,12 | 52 % |
| Normalisé | +0,15 | 55 % |

L'écart va dans le sens attendu (les investisseurs regardent le BPA hors éléments exceptionnels), mais il reste faible et pas statistiquement significatif sur 208 résultats. Les deux surprises restent de mauvais prédicteurs : le marché réagit surtout à ce que le BPA ne mesure pas (chiffre d'affaires, marges, prévisions de la direction).

Cette comparaison utilise le paramètre `methodology` de `Ticker.get_earnings_history()`, que j'ai ajouté à yfinance ([ranaroussi/yfinance#2999](https://github.com/ranaroussi/yfinance/pull/2999), intégré à la branche `dev`). `python gaap.py AMZN` affiche le détail pour une entreprise.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py          # Amazon par défaut
python main.py AAPL     # ou n'importe quel ticker Yahoo Finance
python multi.py         # 54 entreprises, enregistre data/reactions.csv
python scatter.py       # nuage de points -> scatter.png
python gaap.py          # bonus GAAP vs normalisé
streamlit run app.py    # application web
```

`requirements.txt` installe yfinance depuis la branche `dev` du dépôt officiel, en attendant la prochaine version publiée sur PyPI qui inclura le paramètre `methodology` (nécessaire pour le bonus seulement).

## Feuille de route

1. ✅ Une seule action : les 8 derniers résultats
2. ✅ Plusieurs actions : une bonne surprise fait-elle monter l'action ?
3. ✅ Graphique : nuage de points surprise vs réaction
4. ✅ Application web Streamlit : on tape le nom d'une entreprise, l'analyse s'affiche
5. ✅ Bonus : comparer les BPA GAAP et normalisés (non-GAAP), via le paramètre `methodology` ajouté à yfinance

## Données

Données issues de Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance). Projet pédagogique, pas un conseil en investissement.
