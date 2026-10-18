"""Earnings Surprise — bonus : BPA GAAP vs BPA normalisé.

Le BPA GAAP (comptable) inclut les éléments exceptionnels : plus-values sur
participations, dépréciations, coûts de restructuration… Le BPA normalisé
(non-GAAP) les retire. Laquelle des deux surprises la bourse regarde-t-elle ?

Nécessite le paramètre `methodology` de Ticker.get_earnings_history(),
ajouté à yfinance (ranaroussi/yfinance#2999, branche dev).
"""

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

import multi
from main import earnings_reactions

CSV_PATH = Path(__file__).parent / "data" / "gaap_vs_normalized.csv"


def eps_history(ticker: str, methodology: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).get_earnings_history(methodology=methodology)
    except TypeError as e:
        raise RuntimeError(
            "Cette version de yfinance ne gère pas `methodology`. Installer : "
            "pip install git+https://github.com/ranaroussi/yfinance.git@dev"
        ) from e


def gaap_vs_normalized(ticker: str) -> pd.DataFrame:
    gaap = eps_history(ticker, "gaap")
    norm = eps_history(ticker, "normalized")
    if gaap is None or gaap.empty or norm is None or norm.empty:
        raise ValueError(f"Pas d'historique GAAP/normalisé pour {ticker}")

    df = pd.DataFrame({
        "BPA GAAP": gaap["epsActual"],
        "Surprise GAAP (%)": gaap["surprisePercent"] * 100,
        "BPA normalisé": norm["epsActual"],
        "Surprise normalisée (%)": norm["surprisePercent"] * 100,
    })
    df.index = pd.to_datetime(df.index)
    df.index.name = "Fin de trimestre"

    # Rattache chaque trimestre à la première annonce qui suit sa clôture
    reactions = earnings_reactions(ticker, 8)
    reactions.index = pd.to_datetime(reactions.index)
    dates, moves = [], []
    for quarter_end in df.index:
        after = reactions[(reactions.index > quarter_end)
                          & (reactions.index <= quarter_end + pd.Timedelta(days=100))]
        if after.empty:
            dates.append(pd.NaT)
            moves.append(float("nan"))
        else:
            first = after.sort_index().iloc[0]
            dates.append(first.name.date())
            moves.append(first["Réaction (%)"])
    df["Annonce"] = dates
    df["Réaction (%)"] = moves
    return df.sort_index(ascending=False)


def collect(tickers=multi.TICKERS) -> pd.DataFrame:
    frames = []
    for ticker, name in tickers.items():
        try:
            df = gaap_vs_normalized(ticker).reset_index()
        except RuntimeError:
            raise
        except Exception as e:
            print(f"  {ticker} ignoré : {e}", file=sys.stderr)
            continue
        df.insert(0, "Entreprise", name)
        df.insert(0, "Ticker", ticker)
        frames.append(df)
    return pd.concat(frames, ignore_index=True).dropna(subset=["Réaction (%)"])


def compare(data: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque définition : corrélation de rangs et accord de sens avec la réaction."""
    rows = {}
    for label, col in [("GAAP", "Surprise GAAP (%)"), ("Normalisé", "Surprise normalisée (%)")]:
        d = data.dropna(subset=[col])
        same_sign = (d[col] > 0) == (d["Réaction (%)"] > 0)
        rows[label] = {
            "Résultats": len(d),
            "Corrélation (rangs)": d[col].rank().corr(d["Réaction (%)"].rank()),
            "Même sens que la bourse": same_sign.mean(),
        }
    return pd.DataFrame(rows).T.astype({"Résultats": int})


def main():
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 200,
                               "display.max_columns", None):
            print(f"\n{ticker} — BPA GAAP vs normalisé\n")
            print(gaap_vs_normalized(ticker))
        return

    print(f"Récupération de {len(multi.TICKERS)} actions…")
    data = collect()
    CSV_PATH.parent.mkdir(exist_ok=True)
    data.to_csv(CSV_PATH, index=False)

    gap = (data["Surprise GAAP (%)"] - data["Surprise normalisée (%)"]).abs()
    print(f"\n{len(data)} résultats, dont {(gap > 10).sum()} où les deux surprises "
          f"diffèrent de plus de 10 points, et {((data['Surprise GAAP (%)'] > 0) != (data['Surprise normalisée (%)'] > 0)).sum()} "
          f"où elles sont de signe opposé.\n")
    with pd.option_context("display.float_format", "{:,.2f}".format):
        print(compare(data))
    print(f"\nDétail enregistré dans {CSV_PATH}")


if __name__ == "__main__":
    main()
