"""Earnings Surprise — étape 3 : nuage de points.

Surprise de BPA (%) en abscisse, réaction de l'action (%) en ordonnée.
Lit data/reactions.csv (créé par multi.py, relancé si absent) et
enregistre scatter.png.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import multi

OUT_PATH = Path(__file__).parent / "scatter.png"
X_MAX = 50  # au-delà, la surprise est écrasée par un BPA prévu proche de 0
X_MIN = -30

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"
GRID = "#e4e3df"
GROUPS = {  # couleur + forme, pour ne pas dépendre de la couleur seule
    "États-Unis": {"color": "#2a78d6", "marker": "o"},
    "Europe": {"color": "#eb6834", "marker": "s"},
}


def load() -> pd.DataFrame:
    if multi.CSV_PATH.exists():
        return pd.read_csv(multi.CSV_PATH)
    data = multi.collect()
    multi.CSV_PATH.parent.mkdir(exist_ok=True)
    data.to_csv(multi.CSV_PATH, index=False)
    return data


def plot(data: pd.DataFrame, path: Path = OUT_PATH):
    data = data.copy()
    data["Zone"] = data["Ticker"].map(lambda t: "Europe" if "." in t else "États-Unis")

    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    # Quadrants : la surprise et la réaction vont-elles dans le même sens ?
    ax.axhline(0, color=TEXT_MUTED, lw=1, zorder=1)
    ax.axvline(0, color=TEXT_MUTED, lw=1, zorder=1)
    ax.grid(color=GRID, lw=0.8, zorder=0)

    # Surprises hors échelle (BPA prévu proche de 0) : posées sur le bord du graphique
    x = data["Surprise (%)"].clip(X_MIN, X_MAX)
    outside = (data["Surprise (%)"] < X_MIN) | (data["Surprise (%)"] > X_MAX)

    for zone, style in GROUPS.items():
        g = data["Zone"] == zone
        ax.scatter(x[g & ~outside], data.loc[g & ~outside, "Réaction (%)"], s=45,
                   color=style["color"], marker=style["marker"],
                   edgecolor=SURFACE, linewidth=1.2, alpha=0.8, zorder=3,
                   label=f"{zone} ({g.sum()} résultats)")
        ax.scatter(x[g & outside], data.loc[g & outside, "Réaction (%)"], s=45,
                   color=style["color"], marker="D", edgecolor=SURFACE,
                   linewidth=1.2, alpha=0.8, zorder=3)

    # Réaction moyenne par tranche de surprise
    bins = [-np.inf, -10, -5, 0, 5, 10, 20, np.inf]
    centers = [-15, -7.5, -2.5, 2.5, 7.5, 15, 30]
    means = data.groupby(pd.cut(data["Surprise (%)"], bins), observed=False)["Réaction (%)"].mean()
    ax.plot(centers, means.values, color=TEXT, lw=2, marker="o", ms=7,
            markerfacecolor=SURFACE, markeredgewidth=2, zorder=4,
            label="Réaction moyenne par tranche de surprise")
    for cx, m in zip(centers, means.values):
        ax.annotate(f"{m:+.1f} %", (cx, m), xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=8.5, color=TEXT, fontweight="bold", zorder=5)

    if outside.any():
        ax.scatter([], [], s=45, color=TEXT_MUTED, marker="D",
                   label=f"Surprise hors échelle, posée sur le bord ({outside.sum()})")

    beats = data[data["Surprise (%)"] > 0]
    misses = data[data["Surprise (%)"] < 0]
    ax.set_title("Battre les prévisions ne suffit pas à faire monter l'action",
                 loc="left", fontsize=14, color=TEXT, pad=28, fontweight="bold")
    ax.text(0, 1.02,
            f"{len(data)} résultats, {data['Ticker'].nunique()} entreprises. Bonne surprise : l'action bat "
            f"son indice {(beats['Réaction (%)'] > 0).mean():.0%} du temps. Mauvaise : elle fait pire "
            f"{(misses['Réaction (%)'] < 0).mean():.0%} du temps.",
            transform=ax.transAxes, fontsize=9.5, color=TEXT_MUTED)

    ax.set_xlim(X_MIN - 3, X_MAX + 3)
    ax.set_xlabel("Surprise sur le BPA (%) — réel vs prévu par les analystes", color=TEXT_MUTED)
    ax.set_ylabel("Réaction vs marché (%) — action moins son indice", color=TEXT_MUTED)
    ax.tick_params(colors=TEXT_MUTED, length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.legend(loc="lower right", frameon=True, facecolor=SURFACE, edgecolor=GRID, framealpha=0.95, labelcolor=TEXT, fontsize=9)

    fig.text(0.01, 0.01, "Source : Yahoo Finance (yfinance). Réaction = variation de l’action − variation de son indice (S&P 500, CAC 40, DAX…).",
             fontsize=8, color=TEXT_MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    print(f"Graphique enregistré dans {path}")


if __name__ == "__main__":
    plot(load())
