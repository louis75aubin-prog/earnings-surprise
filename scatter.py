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
X_MIN = -25

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

    for zone, style in GROUPS.items():
        g = data[data["Zone"] == zone]
        inside = g[g["Surprise (%)"] <= X_MAX]
        ax.scatter(inside["Surprise (%)"], inside["Réaction (%)"], s=55,
                   color=style["color"], marker=style["marker"],
                   edgecolor=SURFACE, linewidth=1.5, alpha=0.9, zorder=3,
                   label=f"{zone} ({len(g)} résultats)")
        # Surprises hors échelle : posées sur le bord droit, avec leur vraie valeur
        for _, r in g[g["Surprise (%)"] > X_MAX].iterrows():
            ax.scatter(X_MAX, r["Réaction (%)"], s=70, color=style["color"],
                       marker=">", edgecolor=SURFACE, linewidth=1.5, zorder=3)
            ax.annotate(f"{r['Entreprise']} +{r['Surprise (%)']:.0f} %",
                        (X_MAX, r["Réaction (%)"]), xytext=(-8, 0),
                        textcoords="offset points", ha="right", va="center",
                        fontsize=8, color=TEXT_MUTED)

    # Tendance (moindres carrés, sur les points à l'échelle)
    core = data[data["Surprise (%)"] <= X_MAX]
    slope, intercept = np.polyfit(core["Surprise (%)"], core["Réaction (%)"], 1)
    xs = [X_MIN, X_MAX]
    ax.plot(xs, [slope * x + intercept for x in xs], color=TEXT_MUTED,
            lw=2, ls="--", zorder=2, label="Tendance")

    beats = data[data["Surprise (%)"] > 0]
    misses = data[data["Surprise (%)"] < 0]
    ax.set_title("Battre les prévisions ne suffit pas à faire monter l'action",
                 loc="left", fontsize=14, color=TEXT, pad=28, fontweight="bold")
    ax.text(0, 1.02,
            f"{len(data)} résultats trimestriels, {data['Ticker'].nunique()} entreprises. "
            f"Bonne surprise → hausse dans {(beats['Réaction (%)'] > 0).mean():.0%} des cas ; "
            f"mauvaise surprise → baisse dans {(misses['Réaction (%)'] < 0).mean():.0%} des cas.",
            transform=ax.transAxes, fontsize=9.5, color=TEXT_MUTED)

    ax.set_xlim(X_MIN, X_MAX + 3)
    ax.set_xlabel("Surprise sur le BPA (%) — réel vs prévu par les analystes", color=TEXT_MUTED)
    ax.set_ylabel("Réaction de l'action (%) — première séance après l'annonce", color=TEXT_MUTED)
    ax.tick_params(colors=TEXT_MUTED, length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=9)

    fig.text(0.01, 0.01, "Source : Yahoo Finance via yfinance. Cours ajustés.",
             fontsize=8, color=TEXT_MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    print(f"Graphique enregistré dans {path}")


if __name__ == "__main__":
    plot(load())
