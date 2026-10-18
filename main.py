"""Earnings Surprise — étape 1 : une seule action.

Pour un ticker donné, affiche les N derniers résultats trimestriels :
bénéfice par action (BPA) prévu, BPA réel, surprise en %, et réaction
de l'action à la première séance qui suit l'annonce.
"""

import sys

import pandas as pd
import yfinance as yf


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

    start = earnings.index.min().date() - pd.Timedelta(days=10)
    prices = t.history(start=start, auto_adjust=True)["Close"]
    # Yahoo donne les heures d'annonce en heure de New York, même pour les
    # actions européennes : on les ramène dans le fuseau de la place de cotation.
    exchange_tz = prices.index.tz
    if str(exchange_tz).startswith("America/"):
        market_open, market_close = (9, 30), (16, 0)
    else:
        market_open, market_close = (9, 0), (17, 30)
    prices.index = prices.index.date

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
            reaction = float("nan")
        else:
            reaction = (prices[after[0]] / prices[before[-1]] - 1) * 100

        rows.append({
            "Date": day,
            "Moment": moment,
            "BPA prévu": row["EPS Estimate"],
            "BPA réel": row["Reported EPS"],
            "Surprise (%)": surprise_pct(row),
            "Réaction (%)": reaction,
        })

    return pd.DataFrame(rows).set_index("Date").sort_index(ascending=False)


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AMZN"
    df = earnings_reactions(ticker)

    print(f"\n{ticker} — {len(df)} derniers résultats\n")
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 120):
        print(df)

    beats = df[df["Surprise (%)"] > 0]
    if len(beats):
        up = (beats["Réaction (%)"] > 0).sum()
        print(f"\nBonnes surprises : {len(beats)}/{len(df)}, "
              f"dont {up} suivies d'une hausse de l'action.")


if __name__ == "__main__":
    main()
