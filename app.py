"""Earnings Surprise — étape 4 : application web.

Lancer avec :  streamlit run app.py
"""

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf

import gaap
import multi
from main import benchmark_for, earnings_reactions

BLUE = "#2a78d6"
ORANGE = "#eb6834"

st.set_page_config(page_title="Earnings Surprise", page_icon="📈", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def search(query: str) -> list[tuple[str, str]]:
    quotes = yf.Search(query, max_results=8, news_count=0).quotes
    return [(q["symbol"], q.get("shortname") or q.get("longname") or q["symbol"])
            for q in quotes if q.get("quoteType") == "EQUITY"]


@st.cache_data(ttl=3600, show_spinner=False)
def load_reactions(ticker: str, n: int) -> pd.DataFrame:
    return earnings_reactions(ticker, n).reset_index()


@st.cache_data(ttl=3600, show_spinner=False)
def load_gaap(ticker: str) -> pd.DataFrame:
    return gaap.gaap_vs_normalized(ticker).reset_index()


def scatter(df: pd.DataFrame, x: str, color: str = BLUE, tooltip_extra=()) -> alt.Chart:
    base = alt.Chart(df)
    points = base.mark_circle(size=110, color=color, opacity=0.9, stroke="white", strokeWidth=1.5).encode(
        x=alt.X(x, title="Surprise sur le BPA (%)"),
        y=alt.Y("Réaction (%):Q", title="Réaction vs marché (%)"),
        tooltip=[*tooltip_extra,
                 alt.Tooltip(x, format="+.1f"),
                 alt.Tooltip("Réaction (%):Q", format="+.2f")],
    )
    zero_x = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color="#8a8984").encode(x="v:Q")
    zero_y = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color="#8a8984").encode(y="v:Q")
    return (zero_x + zero_y + points).properties(height=380)


def colored(v: float) -> str:
    if pd.isna(v):
        return ""
    return "color: #1a8a3a" if v > 0 else "color: #c0392b" if v < 0 else ""


st.title("Earnings Surprise")
st.markdown("**Quand une entreprise annonce des bénéfices meilleurs (ou pires) que prévu, "
            "comment réagit son action en bourse ?**")


def single_stock():
    col_q, col_pick, col_n = st.columns([2, 3, 1])
    query = col_q.text_input("Nom de l'entreprise ou ticker", value="Amazon")
    try:
        matches = search(query) if query.strip() else []
    except Exception as e:
        st.error(f"Yahoo Finance ne répond pas pour l'instant ({e}). Réessayer dans quelques minutes.")
        return
    if not matches:
        st.warning("Aucune action trouvée pour cette recherche.")
        return
    ticker = col_pick.selectbox(
        "Action", matches, format_func=lambda m: f"{m[1]} ({m[0]})")[0]
    n = col_n.number_input("Résultats", min_value=4, max_value=20, value=8)

    try:
        with st.spinner(f"Récupération des résultats de {ticker}…"):
            df = load_reactions(ticker, int(n))
    except Exception as e:
        st.error(f"{e}. Essayer une autre cotation dans la liste, ou une autre entreprise.")
        return
    df = df.dropna(subset=["Surprise (%)"])
    if df.empty:
        st.error(f"Yahoo Finance n'a pas d'historique de BPA prévu/réel pour {ticker}.")
        return

    beats = df[df["Surprise (%)"] > 0]
    misses = df[df["Surprise (%)"] < 0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Bonnes surprises", f"{len(beats)} / {len(df)}")
    m2.metric("… l'action bat son indice",
              f"{(beats['Réaction (%)'] > 0).sum()} / {len(beats)}" if len(beats) else "–")
    m3.metric("Réaction moy. si bonne", f"{beats['Réaction (%)'].mean():+.2f} %" if len(beats) else "–")
    m4.metric("Réaction moy. si mauvaise", f"{misses['Réaction (%)'].mean():+.2f} %" if len(misses) else "–")

    left, right = st.columns([3, 2])
    left.dataframe(
        df.style.format({"BPA prévu": "{:.2f}", "BPA réel": "{:.2f}",
                         "Surprise (%)": "{:+.1f}", "Action (%)": "{:+.2f}",
                         "Marché (%)": "{:+.2f}", "Réaction (%)": "{:+.2f}"}, na_rep="–")
          .map(colored, subset=["Surprise (%)", "Réaction (%)"]),
        hide_index=True, use_container_width=True)
    right.altair_chart(scatter(df, "Surprise (%):Q", tooltip_extra=["Date:T"]),
                       use_container_width=True)
    st.caption(f"Action : variation entre la clôture qui précède l'annonce et celle de la première "
               f"séance qui suit (fenêtre de deux séances si l'heure d'annonce est incertaine). "
               f"Marché : variation de l'indice de référence ({benchmark_for(ticker) or 'aucun'}) "
               f"sur la même fenêtre. Réaction = Action − Marché.")

    st.subheader("Bonus : BPA GAAP vs normalisé")
    st.markdown("Le BPA **GAAP** est le chiffre comptable, éléments exceptionnels compris "
                "(plus-values, dépréciations, restructurations). Le BPA **normalisé** les retire. "
                "Les deux surprises peuvent raconter des histoires très différentes.")
    try:
        g = load_gaap(ticker)
    except RuntimeError as e:
        st.info(str(e))
    except Exception as e:
        st.info(f"Pas de données GAAP/normalisé pour {ticker} ({e}).")
    else:
        g["Fin de trimestre"] = g["Fin de trimestre"].dt.date
        st.dataframe(
            g.style.format({"BPA GAAP": "{:.2f}", "BPA normalisé": "{:.2f}",
                            "Surprise GAAP (%)": "{:+.1f}", "Surprise normalisée (%)": "{:+.1f}",
                            "Réaction (%)": "{:+.2f}"}, na_rep="–")
             .map(colored, subset=["Surprise GAAP (%)", "Surprise normalisée (%)", "Réaction (%)"]),
            hide_index=True, use_container_width=True)
        opposite = ((g["Surprise GAAP (%)"] > 0) != (g["Surprise normalisée (%)"] > 0)).sum()
        if opposite:
            st.warning(f"{opposite} trimestre(s) où la surprise GAAP et la surprise normalisée "
                       "sont de signe opposé.")


def all_stocks():
    if not multi.CSV_PATH.exists():
        st.info("Lancer d'abord `python multi.py` pour constituer l'échantillon.")
        return
    data = pd.read_csv(multi.CSV_PATH)
    beats = data[data["Surprise (%)"] > 0]
    misses = data[data["Surprise (%)"] < 0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Résultats analysés", f"{len(data)} ({data['Ticker'].nunique()} entreprises)")
    c2.metric("Bonne surprise → bat le marché", f"{(beats['Réaction (%)'] > 0).mean():.0%}")
    c3.metric("Mauvaise surprise → fait pire", f"{(misses['Réaction (%)'] < 0).mean():.0%}")

    clipped = data[data["Surprise (%)"].between(-25, 50)]
    st.altair_chart(scatter(clipped, "Surprise (%):Q", tooltip_extra=["Entreprise:N", "Date:T"]),
                    use_container_width=True)
    st.caption(f"{len(data) - len(clipped)} surprises extrêmes (BPA prévu proche de 0) "
               "hors du graphique, mais comptées dans les chiffres.")
    st.dataframe(multi.summarize(data).style.format(precision=2), use_container_width=True)

    if gaap.CSV_PATH.exists():
        st.subheader("GAAP ou normalisé : quelle surprise la bourse suit-elle ?")
        st.dataframe(gaap.compare(pd.read_csv(gaap.CSV_PATH))
                     .style.format({"Corrélation (rangs)": "{:+.2f}",
                                    "Même sens que la bourse": "{:.0%}"}),
                     use_container_width=True)


tab_one, tab_all = st.tabs(["Une action", "Toutes les entreprises"])
with tab_one:
    single_stock()
with tab_all:
    all_stocks()
