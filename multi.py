"""Earnings Surprise — étape 2 : plusieurs actions.

Applique l'analyse de main.py à une cinquantaine de grandes entreprises
américaines et européennes et répond à la question : une bonne surprise
fait-elle vraiment monter l'action ?
Les résultats détaillés sont enregistrés dans data/reactions.csv.

L'échantillon regroupe les grandes capitalisations pour lesquelles Yahoo
Finance publie un historique trimestriel de BPA prévu/réel. Beaucoup de
valeurs du CAC 40 (LVMH, L'Oréal, Hermès, Safran, Schneider…) n'en ont pas.
"""

import sys
from pathlib import Path

import pandas as pd

from main import earnings_reactions

US = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "NVDA": "Nvidia", "META": "Meta", "TSLA": "Tesla", "AVGO": "Broadcom",
    "ORCL": "Oracle", "ADBE": "Adobe", "CRM": "Salesforce", "AMD": "AMD",
    "INTC": "Intel", "NFLX": "Netflix", "JPM": "JPMorgan", "BAC": "Bank of America",
    "V": "Visa", "MA": "Mastercard", "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson",
    "LLY": "Eli Lilly", "PFE": "Pfizer", "MRK": "Merck", "ABBV": "AbbVie",
    "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo", "WMT": "Walmart",
    "COST": "Costco", "HD": "Home Depot", "MCD": "McDonald's", "NKE": "Nike",
    "DIS": "Disney", "XOM": "ExxonMobil", "CVX": "Chevron",
}
EUROPE = {
    "TTE.PA": "TotalEnergies", "AIR.PA": "Airbus", "SAN.PA": "Sanofi",
    "BNP.PA": "BNP Paribas", "GLE.PA": "Société Générale", "ACA.PA": "Crédit Agricole",
    "DSY.PA": "Dassault Systèmes", "LR.PA": "Legrand", "EN.PA": "Bouygues",
    "STMPA.PA": "STMicroelectronics", "MT.AS": "ArcelorMittal", "ASML.AS": "ASML",
    "SAP.DE": "SAP", "SIE.DE": "Siemens", "ALV.DE": "Allianz",
    "NOVO-B.CO": "Novo Nordisk", "AZN.L": "AstraZeneca", "SHEL.L": "Shell",
    "HSBA.L": "HSBC",
}
TICKERS = {**US, **EUROPE}

CSV_PATH = Path(__file__).parent / "data" / "reactions.csv"


def collect(tickers=TICKERS, n: int = 8) -> pd.DataFrame:
    frames = []
    for ticker, name in tickers.items():
        try:
            df = earnings_reactions(ticker, n)
        except Exception as e:
            print(f"  {ticker} ignoré : {e}", file=sys.stderr)
            continue
        df = df.reset_index()
        df.insert(0, "Entreprise", name)
        df.insert(0, "Ticker", ticker)
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    return data.dropna(subset=["Surprise (%)", "Réaction (%)"])


def summarize(data: pd.DataFrame) -> pd.DataFrame:
    def stats(g):
        beats = g[g["Surprise (%)"] > 0]
        misses = g[g["Surprise (%)"] < 0]
        return pd.Series({
            "Résultats": len(g),
            "Bonnes surprises": len(beats),
            "dont hausse": (beats["Réaction (%)"] > 0).sum(),
            "Réaction moy. si bonne (%)": beats["Réaction (%)"].mean(),
            "Réaction moy. si mauvaise (%)": misses["Réaction (%)"].mean(),
            "Corrélation (rangs)": rank_corr(g),
        })

    summary = data.groupby("Entreprise", sort=False).apply(stats, include_groups=False)
    counts = ["Résultats", "Bonnes surprises", "dont hausse"]
    return summary.astype({c: int for c in counts})


def rank_corr(df: pd.DataFrame) -> float:
    # Corrélation de Spearman : robuste aux surprises extrêmes (BPA prévu proche de 0)
    return df["Surprise (%)"].rank().corr(df["Réaction (%)"].rank())


def main():
    print(f"Récupération de {len(TICKERS)} actions…")
    data = collect()
    CSV_PATH.parent.mkdir(exist_ok=True)
    data.to_csv(CSV_PATH, index=False)

    summary = summarize(data)
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 200, "display.max_columns", None):
        print()
        print(summary)

    beats = data[data["Surprise (%)"] > 0]
    misses = data[data["Surprise (%)"] < 0]
    print(f"\nSur {len(data)} résultats :")
    print(f"  bonnes surprises : {len(beats)}, suivies d'une hausse dans "
          f"{(beats['Réaction (%)'] > 0).mean():.0%} des cas "
          f"(réaction moyenne {beats['Réaction (%)'].mean():+.2f} %)")
    if len(misses):
        print(f"  mauvaises surprises : {len(misses)}, suivies d'une baisse dans "
              f"{(misses['Réaction (%)'] < 0).mean():.0%} des cas "
              f"(réaction moyenne {misses['Réaction (%)'].mean():+.2f} %)")
    print(f"  corrélation surprise / réaction (rangs) : {rank_corr(data):+.2f}")
    print(f"\nDétail enregistré dans {CSV_PATH}")


if __name__ == "__main__":
    main()
