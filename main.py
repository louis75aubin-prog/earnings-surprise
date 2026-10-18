"""Earnings Surprise — étape 1 : une seule action.

Pour un ticker donné, affiche les N derniers résultats trimestriels :
bénéfice par action (BPA) prévu, BPA réel, surprise en %, et réaction
de l'action à la première séance qui suit l'annonce.

La réaction est mesurée par rapport au marché : variation de l'action moins
variation de son indice de référence sur la même fenêtre (rendement anormal).
Si le Nasdaq prend +2 % le jour où Amazon prend +9 %, la réaction aux
résultats est de +7 %.
"""

import sys

import pandas as pd
import yfinance as yf


# Heures d'ouverture et de clôture, en heure locale de la place de cotation
MARKET_HOURS = {
    "America/New_York": ((9, 30), (16, 0)),
    "Europe/London": ((8, 0), (16, 30)),
    "Europe/Copenhagen": ((9, 0), (17, 0)),
    "Europe/Zurich": ((9, 0), (17, 30)),
    "default": ((9, 0), (17, 30)),  # Paris, Amsterdam, Francfort…
}


# Indice de référence selon la place de cotation (suffixe du ticker Yahoo)
BENCHMARKS = {
    "": "^GSPC",  # S&P 500 pour les actions américaines (pas de suffixe)
    "PA": "^FCHI", "AS": "^AEX", "DE": "^GDAXI", "L": "^FTSE", "CO": "^OMXC25",
    "SW": "^SSMI", "MI": "FTSEMIB.MI", "MC": "^IBEX", "TO": "^GSPTSE",
    "T": "^N225", "HK": "^HSI",
}


def benchmark_for(ticker: str) -> str | None:
    suffix = ticker.rsplit(".", 1)[1] if "." in ticker else ""
    return BENCHMARKS.get(suffix)


def window_return(prices: pd.Series, start, end) -> float:
    """Variation (%) entre la clôture du `start` (ou la précédente) et celle du `end` (ou la suivante)."""
    before = prices[prices.index <= start]
    after = prices[prices.index >= end]
    if before.empty or after.empty:
        return float("nan")
    return (after.iloc[0] / before.iloc[-1] - 1) * 100


def surprise_pct(row) -> float:
    """Surprise fournie par Yahoo, ou recalculée si elle manque."""
    if pd.notna(row["Surprise(%)"]):
        return row["Surprise(%)"]
    est, actual = row["EPS Estimate"], row["Reported EPS"]
    if pd.isna(est) or est == 0:
        return float("nan")
    return (actual - est) / abs(est) * 100


def earnings_reactions(ticker: str, n: int = 8) -> pd.DataFrame:
    t = yf.Ticker(ticker)

    earnings = t.get_earnings_dates(limit=n + 8)
    if earnings is None or earnings.empty:
        raise ValueError(f"Aucune date de résultats trouvée pour {ticker}")
    # On ne garde que les résultats déjà publiés
    earnings = earnings.dropna(subset=["Reported EPS"]).sort_index().tail(n)
    if earnings.empty:
        raise ValueError(f"Yahoo Finance n'a pas d'historique de BPA publié pour {ticker}")

    start = earnings.index.min().date() - pd.Timedelta(days=10)
    prices = t.history(start=start, auto_adjust=True)["Close"]
    # Yahoo donne les heures d'annonce en heure de New York, même pour les
    # actions européennes : on les ramène dans le fuseau de la place de cotation.
    exchange_tz = prices.index.tz
    market_open, market_close = MARKET_HOURS.get(str(exchange_tz), MARKET_HOURS["default"])
    prices.index = prices.index.date

    index_ticker = benchmark_for(ticker)
    index_prices = None
    if index_ticker:
        index_prices = yf.Ticker(index_ticker).history(start=start, auto_adjust=True)["Close"]
        index_prices.index = index_prices.index.date

    rows = []
    for ts, row in earnings.iterrows():
        ts = ts.tz_convert(exchange_tz)
        day = ts.date()
        hm = (ts.hour, ts.minute)
        # Avant l'ouverture : clôture du jour J vs clôture de la veille.
        # Après la clôture : clôture du lendemain vs clôture du jour J.
        # Pendant la séance (souvent une heure approximative chez Yahoo) :
        # on prend large, clôture du lendemain vs clôture de la veille.
        if hm < market_open:
            moment = "avant ouverture"
        elif hm >= market_close:
            moment = "après clôture"
        else:
            moment = "heure incertaine"
        before = [d for d in prices.index if (d <= day if moment == "après clôture" else d < day)]
        after = [d for d in prices.index if (d >= day if moment == "avant ouverture" else d > day)]
        if not before or not after:
            stock_move = market_move = float("nan")
        else:
            stock_move = window_return(prices, before[-1], after[0])
            market_move = (window_return(index_prices, before[-1], after[0])
                           if index_prices is not None else float("nan"))
        # Sans indice connu pour cette place, on garde la variation brute
        reaction = stock_move - market_move if pd.notna(market_move) else stock_move

        rows.append({
            "Date": day,
            "Moment": moment,
            "BPA prévu": row["EPS Estimate"],
            "BPA réel": row["Reported EPS"],
            "Surprise (%)": surprise_pct(row),
            "Action (%)": stock_move,
            "Marché (%)": market_move,
            "Réaction (%)": reaction,
        })

    return pd.DataFrame(rows).set_index("Date").sort_index(ascending=False)


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AMZN"
    df = earnings_reactions(ticker)

    print(f"\n{ticker} — {len(df)} derniers résultats "
          f"(réaction = action − {benchmark_for(ticker) or 'aucun indice'})\n")
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 160, "display.max_columns", None):
        print(df)

    beats = df[df["Surprise (%)"] > 0]
    if len(beats):
        up = (beats["Réaction (%)"] > 0).sum()
        print(f"\nBonnes surprises : {len(beats)}/{len(df)}, "
              f"dont {up} suivies d'une hausse de l'action par rapport au marché.")


if __name__ == "__main__":
    main()
