"""
Steady — make peace with market risk.

A calm companion for the nervous first-time investor.
Built on real S&P 500 total returns from 2000-2025 (dividends reinvested) —
the market you've actually lived in.

Educational only — not financial advice.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- setup

st.set_page_config(
    page_title="Steady — make peace with market risk",
    page_icon="🌿",
    layout="wide",
)

GREEN = "#4C8C6A"
RED = "#C97064"
BLUE = "#6B8FB3"
GRAY = "#9AA5B1"
GOLD = "#D9A05B"
PAPER = "rgba(0,0,0,0)"

START_YEAR = 2000  # the modern market: index funds, online brokers, you

# Published long-run frequencies (Shiller / S&P data, widely documented).
# Day- and month-level stats can't be computed from annual data, so we
# use the standard published figures and compute everything else ourselves.
PCT_DAYS_DOWN = 0.47
PCT_MONTHS_DOWN = 0.37


@st.cache_data
def load_returns() -> pd.DataFrame:
    df = pd.read_csv(Path(__file__).parent / "data" / "sp500_annual_total_returns.csv")
    df = df[df["Year"] >= START_YEAR].reset_index(drop=True)
    df["r"] = df["TotalReturnPct"] / 100.0
    return df


def money(x: float) -> str:
    return f"${x:,.0f}"


def calm_layout(fig: go.Figure, dollars: bool = False, **kwargs) -> go.Figure:
    fig.update_layout(
        plot_bgcolor=PAPER,
        paper_bgcolor=PAPER,
        font=dict(family="Georgia, serif", size=14),
        margin=dict(l=10, r=30, t=50, b=10),
        **kwargs,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(154,165,177,0.25)")
    if dollars:
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


df = load_returns()
YEARS = df["Year"].tolist()
RET = df.set_index("Year")["r"]
FIRST, LAST = min(YEARS), max(YEARS)
N_YEARS_DATA = LAST - FIRST + 1

# ---------------------------------------------------------------- header

st.title("🌿 Steady")
st.markdown(
    "#### A calm look at the modern stock market — for people who are "
    "afraid of losing money."
)
st.markdown(
    f"Everything below uses **real S&P 500 total returns from {FIRST} to "
    f"{LAST}** (dividends reinvested) — the market you've actually lived "
    "through: the dot-com bust, the 2008 crisis, COVID, the 2022 bear. "
    "No live prices, no ticking numbers, nothing to obsess over. Just the "
    "evidence."
)
st.caption(
    "Educational only — not financial advice. Past performance doesn't "
    "guarantee future results."
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "🌱 Start small",
        "⏳ Fast forward",
        "👀 The cost of looking",
        "🌧️ Worst case",
        "🔭 What might happen next",
        "🧺 What's inside the fund",
        "✅ Am I doing this right?",
    ]
)

# ---------------------------------------------------------------- helpers

FREQ_OPTIONS = {
    "Every month": 12,
    "Every other month": 6,
    "Every 3 months": 4,
    "Twice a year": 2,
}

DOLLAR_HOVER = "%{x}: %{y:$,.0f}<extra></extra>"


def until_today(amount: float, per_year: int) -> pd.DataFrame:
    """Contribute `amount` roughly `per_year` times a year, starting in each
    possible year and continuing through the end of the data. Everything is
    valued at the end of the final year. Monthly growth is interpolated
    from each year's real annual return."""
    gap = 12 // per_year
    rows = []
    for start in range(FIRST, LAST + 1):
        val = 0.0
        contributed = 0.0
        month_i = 0
        for y in range(start, LAST + 1):
            m = (1.0 + RET[y]) ** (1.0 / 12.0) - 1.0
            for _ in range(12):
                if month_i % gap == 0:
                    val += amount
                    contributed += amount
                val *= 1.0 + m
                month_i += 1
        rows.append((start, contributed, val))
    return pd.DataFrame(rows, columns=["start", "contributed", "final"])


def growth_path(start_year: int, years: int, amount: float) -> pd.DataFrame:
    """Value of a lump sum at the end of each year, using real returns."""
    vals = [amount]
    yrs = [start_year - 1]
    v = amount
    for y in range(start_year, min(start_year + years, LAST + 1)):
        v *= 1.0 + RET[y]
        vals.append(v)
        yrs.append(y)
    return pd.DataFrame({"year": yrs, "value": vals})


def window_stats(window: int) -> dict:
    """Every historical `window`-year outcome: total growth factors,
    annualized returns, and the share that ended positive."""
    growth = (1.0 + df["r"]).values
    n = len(growth)
    cums = np.array([np.prod(growth[i : i + window]) for i in range(n - window + 1)])
    ann = cums ** (1.0 / window) - 1.0
    return {
        "cums": cums,
        "ann": ann,
        "p_pos": float(np.mean(cums > 1.0)),
        "n": len(cums),
    }


def rolling_positive(window: int) -> float:
    return window_stats(window)["p_pos"]


# ---------------------------------------------------------------- tab 1

with tab1:
    st.subheader("Add what you can, when you can")
    st.markdown(
        "No steady paycheck rhythm required. Pick an amount that doesn't "
        "scare you and a rough rhythm — skipping months is allowed, life "
        "happens. Each bar answers one plain question: **if you'd started "
        f"in that year and kept adding until the end of {LAST}, what would "
        "you have now?** No windows, no cutoffs — every year of data, "
        "ending today."
    )

    c1, c2 = st.columns(2)
    amount1 = c1.select_slider(
        "Amount each time",
        options=[25, 50, 100, 150, 200, 300, 500, 750, 1000],
        value=50,
        format_func=money,
    )
    freq_label = c2.selectbox("Roughly how often?", list(FREQ_OPTIONS))
    per_year = FREQ_OPTIONS[freq_label]

    out = until_today(amount1, per_year)
    out["ratio"] = out["final"] / out["contributed"]
    ahead = float((out["final"] >= out["contributed"]).mean())
    oldest = out.iloc[0]
    worst = out.loc[out["ratio"].idxmin()]
    best = out.loc[out["ratio"].idxmax()]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Starts that are ahead today",
        f"{ahead:.0%}",
        f"of all {len(out)} starting years",
        delta_color="off",
    )
    m2.metric(
        f"Started {int(oldest['start'])}",
        money(oldest["final"]),
        f"put in {money(oldest['contributed'])}",
        delta_color="off",
    )
    m3.metric(
        f"Slowest start ({int(worst['start'])})",
        money(worst["final"]),
        f"{worst['ratio'] - 1:+.0%} vs what went in",
    )
    m4.metric(
        f"Strongest start ({int(best['start'])})",
        money(best["final"]),
        f"{best['ratio'] - 1:+.0%} vs what went in",
    )

    if ahead == 1.0:
        st.markdown(
            f"**Every single starting year since {FIRST} — even 2000, even "
            "2008 — is worth more today than what was put in.** The bars "
            "shrink to the right for one simple reason: less time invested, "
            "less growth. That's the whole lesson — time in, not timing."
        )
    else:
        behind = int((out["final"] < out["contributed"]).sum())
        st.markdown(
            f"**{ahead:.0%} of starting years are ahead today.** The "
            f"{behind} that aren't are the most recent starts — they've "
            "simply had the least time. Time in, not timing."
        )

    fig = go.Figure()
    fig.add_bar(
        x=out["start"],
        y=out["final"],
        marker_color=[
            GREEN if f >= c else RED
            for f, c in zip(out["final"], out["contributed"])
        ],
        customdata=out["contributed"],
        hovertemplate=(
            "Started %{x}: worth %{y:$,.0f} "
            "(put in %{customdata:$,.0f})<extra></extra>"
        ),
        name="worth today",
    )
    fig.add_scatter(
        x=out["start"],
        y=out["contributed"],
        mode="lines",
        line=dict(color=GRAY, dash="dot", shape="hv", width=2),
        hovertemplate="Started %{x}: put in %{y:$,.0f}<extra></extra>",
        name="what you put in",
    )
    calm_layout(
        fig,
        dollars=True,
        title=(
            f"{money(amount1)} {freq_label.lower()}, from each starting "
            f"year to the end of {LAST}"
        ),
        xaxis_title="Year you started",
        yaxis_title=f"Value at the end of {LAST}",
        showlegend=False,
    )
    fig.add_annotation(
        x=out["start"].iloc[0],
        y=float(out["contributed"].iloc[0]),
        text="what you put in",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        yshift=6,
        font=dict(size=12, color=GRAY),
    )
    fig.update_xaxes(tickformat="d")
    st.plotly_chart(fig, width="stretch")

    st.caption(
        f"Every year of data ({FIRST}-{LAST}) is on screen. The dotted "
        "stair is the total you'd have put in from that start — later "
        "starts put in less and have had less time to grow, which is why "
        "the bars shrink. The rhythm is a modeling assumption, not a rule; "
        "what matters is that money you add stays in."
    )

# ---------------------------------------------------------------- tab 2

with tab2:
    st.subheader("Fast forward: your money, years from now")
    st.markdown(
        "No regret math here — no \u201cif only you'd started in 2000.\u201d This "
        "tab points **forward**. Pick what you're thinking of investing and "
        "how long you'd leave it alone. Your money then travels **every "
        "road the modern market has actually taken** over a stretch that "
        "long — all overlaid. Not a prediction: the full set of real "
        "journeys, so you can see the shape of what you'd be signing up for."
    )

    c1, c2 = st.columns(2)
    amount = c1.select_slider(
        "If you invested",
        options=[100, 250, 500, 1000, 2500, 5000, 10000, 25000],
        value=1000,
        format_func=money,
    )
    fwd = c2.slider("…and left it alone for (years)", 5, 20, 10)

    starts = list(range(FIRST, LAST - fwd + 2))
    paths = []
    for s in starts:
        vals = [float(amount)]
        v = float(amount)
        for y in range(s, s + fwd):
            v *= 1.0 + RET[y]
            vals.append(v)
        paths.append(vals)
    endings = np.array([p[-1] for p in paths])
    worst_i = int(endings.argmin())
    best_i = int(endings.argmax())
    med_i = int(np.abs(endings - np.median(endings)).argmin())
    p_pos = float(np.mean(endings >= amount))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Roughest road ever",
        money(endings[worst_i]),
        f"{endings[worst_i] / amount - 1:+.0%}",
    )
    m2.metric(
        "Typical road",
        money(endings[med_i]),
        f"{endings[med_i] / amount - 1:+.0%}",
    )
    m3.metric(
        "Best road ever",
        money(endings[best_i]),
        f"{endings[best_i] / amount - 1:+.0%}",
    )
    m4.metric(
        "Roads that ended ahead",
        f"{p_pos:.0%}",
        f"of {len(starts)} real {fwd}-year journeys",
        delta_color="off",
    )

    xs = list(range(fwd + 1))
    fig = go.Figure()
    for i, vals in enumerate(paths):
        if i in (worst_i, med_i, best_i):
            continue
        fig.add_scatter(
            x=xs,
            y=vals,
            mode="lines",
            line=dict(color="rgba(107,143,179,0.22)", width=1.5),
            hoverinfo="skip",
            showlegend=False,
        )
    for i, color, label in [
        (worst_i, RED, "roughest"),
        (med_i, GOLD, "typical"),
        (best_i, GREEN, "best"),
    ]:
        fig.add_scatter(
            x=xs,
            y=paths[i],
            mode="lines",
            line=dict(color=color, width=3),
            name=f"{label} ({starts[i]}-{starts[i] + fwd})",
            hovertemplate="year %{x}: %{y:$,.0f}<extra>" + label + "</extra>",
        )
    fig.add_hline(
        y=amount,
        line_dash="dot",
        line_color=GRAY,
        annotation_text="what you'd start with",
        annotation_position="bottom right",
    )
    calm_layout(
        fig,
        dollars=True,
        title=(
            f"{money(amount)} riding every real {fwd}-year stretch of the "
            f"modern market ({len(starts)} journeys)"
        ),
        xaxis_title="Years from now",
        yaxis_title="Value",
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0),
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        f"""
Every line is real history wearing your numbers. The wobble in the middle
of even the best roads is normal — **the shape of the ride is drops and
recoveries, and the destination mostly depends on how long you stay on the
road.** Nobody knows which line the future will resemble. But notice what
patience does: hold for {fwd} years and {p_pos:.0%} of every such journey
this market has produced ended above where it started. Try sliding the
years up and watch the floor rise.
"""
    )
    st.caption(
        "History's roads, not a forecast — the future can be better or "
        "worse than anything shown. Dividends reinvested."
    )

# ---------------------------------------------------------------- tab 3

with tab3:
    st.subheader("The market didn't change. How often you looked did.")
    st.markdown(
        "Worried you'd obsessively check your investments? Here's the "
        "thing: **how often you look determines how much losing you "
        "experience** — with the *same* investment and the *same* outcome."
    )

    yrs_check = 10
    pct_years_down = float((df["r"] < 0).mean())
    pct_decades_down = 1.0 - rolling_positive(10)

    freqs = pd.DataFrame(
        [
            ("Every day", 252 * yrs_check, PCT_DAYS_DOWN),
            ("Every month", 12 * yrs_check, PCT_MONTHS_DOWN),
            ("Once a year", yrs_check, pct_years_down),
            ("Once a decade", 1, pct_decades_down),
        ],
        columns=["freq", "looks", "p_red"],
    )
    freqs["red_looks"] = (freqs["looks"] * freqs["p_red"]).round(0).astype(int)

    st.markdown(f"Imagine holding a US index fund for **{yrs_check} years**:")

    cols = st.columns(4)
    for col, (_, row) in zip(cols, freqs.iterrows()):
        col.metric(
            row["freq"],
            f"{row['red_looks']:,} bad moments",
            f"{row['p_red']:.0%} of checks show a loss",
            delta_color="off",
        )

    fig = go.Figure()
    fig.add_bar(
        x=freqs["freq"],
        y=freqs["red_looks"],
        marker_color=[RED, RED, GOLD, GREEN],
        text=freqs["red_looks"].map(lambda v: f"{v:,}"),
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: %{y:,} painful checks<extra></extra>",
    )
    calm_layout(
        fig,
        title="Times you'd see yourself 'losing money' over the same 10 years",
        yaxis_title="Painful moments experienced",
        yaxis_type="log",
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        f"""
Same money. Same decade. Same final result.

- Check **daily** and you witness roughly **{freqs['red_looks'][0]:,} losses**.
- Check **once a year** and it's about **{freqs['red_looks'][2]}**.
- Check **once a decade** and — based on every 10-year stretch since
  {FIRST}, *including* the dot-com lost decade — you'd see a loss only
  **{pct_decades_down:.0%}** of the time.

A *calm, low-movement* system isn't a weakness to fix. It's the
statistically correct way to hold an index fund. Obsessive checking isn't
required — it's actively counterproductive.
"""
    )
    st.caption(
        "Day and month frequencies are long-run published S&P figures; "
        f"year and decade frequencies are computed from the bundled "
        f"{FIRST}-{LAST} dataset."
    )

# ---------------------------------------------------------------- tab 4

with tab4:
    st.subheader("Invest at the worst possible moment. On purpose.")
    st.markdown(
        "The nightmare scenario: you finally invest, and the market "
        "immediately collapses. Let's stop imagining it and actually do it. "
        "Below, $10,000 goes in **right before the modern era's ugliest "
        "crashes** — all of which you lived through."
    )

    crashes = {
        "2000 — Dot-com bust": {
            "year": 2000,
            "depth": "Three straight losing years — the index dropped about "
            "49% from its 2000 peak. The worst possible start of the "
            "modern era.",
        },
        "2008 — Financial crisis": {
            "year": 2008,
            "depth": "The index fell about 55% from late 2007 to March 2009. "
            "It felt like the end of the financial world.",
        },
        "2022 — Inflation bear market": {
            "year": 2022,
            "depth": "Stocks and bonds fell together — the index dropped "
            "about 25% from its peak while inflation hit 40-year highs.",
        },
    }

    choice = st.radio("Choose your disaster", list(crashes.keys()), horizontal=True)
    crash = crashes[choice]
    cy = crash["year"]

    amount4 = 10_000
    path4 = growth_path(cy, LAST - cy + 1, amount4)
    final4 = path4["value"].iloc[-1]

    recovered_year = None
    for _, r in path4.iterrows():
        if r["year"] > cy - 1 and r["value"] >= amount4:
            recovered_year = int(r["year"])
            break
    years_under = (recovered_year - cy + 1) if recovered_year else None

    m1, m2, m3 = st.columns(3)
    m1.metric("Invested", money(amount4), f"start of {cy}")
    m2.metric(
        "Years until whole again",
        f"{years_under}" if years_under else "—",
    )
    m3.metric(
        f"Worth by end of {LAST}",
        money(final4),
        f"{final4 / amount4:.1f}× the money",
    )

    st.info(f"**How bad it got:** {crash['depth']}")

    fig = go.Figure()
    fig.add_scatter(
        x=path4["year"],
        y=path4["value"],
        mode="lines",
        line=dict(color=GREEN, width=3),
        hovertemplate=DOLLAR_HOVER,
    )
    fig.add_hline(
        y=amount4,
        line_dash="dot",
        line_color=GRAY,
        annotation_text="break-even",
        annotation_position="bottom right",
    )
    if recovered_year:
        fig.add_vrect(
            x0=cy - 1,
            x1=recovered_year,
            fillcolor="rgba(201,112,100,0.10)",
            line_width=0,
            annotation_text="underwater",
            annotation_position="top left",
        )
    calm_layout(
        fig,
        dollars=True,
        title=f"{money(amount4)} invested at the start of {cy}, held ever since",
        xaxis_title="Year",
        yaxis_title="Value",
        showlegend=False,
    )
    fig.update_xaxes(tickformat="d")
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        f"""
This is the **worst-case timing** — no one actually invests everything on
the eve of a historic crash, and even *this* person ended up with
**{money(final4)}**. The pain was real, but it was temporary. The growth
was permanent — for the investor who didn't sell.

And remember the previous tab: the person who checked once a year barely
noticed most of this.
"""
    )

# ---------------------------------------------------------------- tab 5

with tab5:
    st.subheader("Not a forecast — every future that's actually happened")
    st.markdown(
        "Nobody can predict the market over months — not banks, not hedge "
        "funds, and definitely not an app. Anyone showing you a specific "
        "number for 'the S&P in 6 months' is guessing. What *can* be shown "
        f"honestly: **every outcome the modern market ({FIRST}-{LAST}) has "
        "ever delivered** over the horizon you choose. Not what *will* "
        "happen — the full range of what's *ever* happened."
    )

    h_list = [1, 3, 5, 10, 15, 20]
    stats = {h: window_stats(h) for h in h_list}

    rng = pd.DataFrame(
        [
            {
                "h": h,
                "label": f"{h} year" + ("s" if h > 1 else ""),
                "lo": float(stats[h]["ann"].min()),
                "med": float(np.median(stats[h]["ann"])),
                "hi": float(stats[h]["ann"].max()),
                "tlo": float(stats[h]["cums"].min()),
                "tmed": float(np.median(stats[h]["cums"])),
                "thi": float(stats[h]["cums"].max()),
                "p_pos": stats[h]["p_pos"],
                "n": stats[h]["n"],
            }
            for h in h_list
        ]
    )

    fig = go.Figure()
    fig.add_bar(
        x=rng["label"],
        y=rng["hi"] - rng["lo"],
        base=rng["lo"],
        marker_color="rgba(107,143,179,0.35)",
        customdata=np.stack([rng["lo"], rng["hi"]], axis=-1),
        hovertemplate=(
            "%{x}: worst %{customdata[0]:.1%} to best "
            "%{customdata[1]:.1%} per year<extra></extra>"
        ),
        name="range",
    )
    fig.add_scatter(
        x=rng["label"],
        y=rng["med"],
        mode="markers",
        marker=dict(color=GOLD, size=13, symbol="diamond"),
        hovertemplate="%{x}: typical %{y:.1%} per year<extra></extra>",
        name="typical",
    )
    fig.add_hline(y=0, line_color=GRAY, line_dash="dot")
    calm_layout(
        fig,
        title="How long you hold decides how wild the ride can be (per-year returns)",
        yaxis_title="Annualized return — full historical range",
        showlegend=False,
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        "**Read it left to right: time squeezes the scary end.** One-year "
        "outcomes are all over the map. By 15-20 years, every stretch the "
        "modern market has ever produced — every single one, crashes "
        "included — ended positive."
    )

    st.markdown("---")
    sel = st.select_slider(
        "Zoom into one horizon — what happened to $1,000?",
        options=h_list,
        value=10,
        format_func=lambda h: f"{h} year" + ("s" if h > 1 else ""),
    )
    row = rng[rng["h"] == sel].iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Worst ever", money(1000 * row["tlo"]), f"{row['tlo'] - 1:+.0%} total"
    )
    m2.metric(
        "Typical", money(1000 * row["tmed"]), f"{row['tmed'] - 1:+.0%} total"
    )
    m3.metric(
        "Best ever", money(1000 * row["thi"]), f"{row['thi'] - 1:+.0%} total"
    )
    m4.metric(
        "Ended positive",
        f"{row['p_pos']:.0%}",
        f"of all {int(row['n'])} such periods",
        delta_color="off",
    )

    st.caption(
        f"Every {sel}-year window between {FIRST} and {LAST}, dividends "
        "reinvested. History's range, not a prediction — the future can "
        "always exceed it in either direction. But notice the pattern: "
        "patience narrows the range, and it narrows upward."
    )

# ---------------------------------------------------------------- tab 6

with tab6:
    st.subheader("Open the box: the 11 ingredients of a US index fund")
    st.markdown(
        "Fear of the unknown is still fear. So here's exactly what you'd "
        "own. A broad US index fund holds every major American company, "
        "sorted into **11 sectors**. You don't pick between them — you own "
        "them all. But knowing what each one is makes the whole thing less "
        "mysterious."
    )

    sectors = [
        ("Information Technology", 32, "Apple, Microsoft, Nvidia",
         "The growth engine — software, chips, the internet itself.",
         "Expensive and dramatic: fell hardest in 2000-02 and dropped ~28% in 2022 before roaring back."),
        ("Financials", 14, "JPMorgan, Berkshire Hathaway, Visa",
         "Banks and payments profit as the economy grows.",
         "Cyclical — ground zero of the 2008 crisis."),
        ("Health Care", 11, "Eli Lilly, UnitedHealth, Johnson & Johnson",
         "Steady demand — illness doesn't care about recessions.",
         "Slower growth; exposed to drug-pricing politics."),
        ("Consumer Discretionary", 10, "Amazon, Tesla, Home Depot",
         "The 'wants' — booms when people feel confident.",
         "First to fall when wallets close in a recession."),
        ("Communication Services", 9, "Alphabet (Google), Meta, Netflix",
         "Attention and advertising at global scale.",
         "Ad budgets are cyclical; a few giants dominate."),
        ("Industrials", 8, "Caterpillar, Boeing, Union Pacific",
         "The physical economy — machines, freight, defense.",
         "Rises and falls with economic activity."),
        ("Consumer Staples", 6, "Procter & Gamble, Costco, Coca-Cola",
         "The 'needs' — toothpaste and groceries in any economy.",
         "Defensive but slow; rarely the star."),
        ("Energy", 3, "ExxonMobil, Chevron",
         "Powers everything; huge dividends when oil is up.",
         "Boom-bust with oil prices: worst sector in 2020 (~-34%), best in 2022 (~+60%)."),
        ("Utilities", 3, "NextEra, Duke Energy",
         "Everyone pays the electric bill — steady dividends.",
         "Slow growth; sensitive to interest rates."),
        ("Real Estate", 2, "Prologis, American Tower",
         "Warehouses, cell towers, offices — rent as income.",
         "Struggles when interest rates rise."),
        ("Materials", 2, "Linde, Sherwin-Williams",
         "The raw stuff — chemicals, metals, building supplies.",
         "Commodity cycles; follows global demand."),
    ]

    sec_df = pd.DataFrame(
        sectors, columns=["sector", "weight", "names", "strength", "weakness"]
    ).sort_values("weight")

    fig = go.Figure()
    fig.add_bar(
        x=sec_df["weight"],
        y=sec_df["sector"],
        orientation="h",
        marker_color=BLUE,
        text=sec_df["weight"].map(lambda w: f"~{w}%"),
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: ~%{x}% of the index<extra></extra>",
    )
    calm_layout(
        fig,
        title="Roughly how a US index fund divides your money (approx. weights)",
        xaxis_title="Share of the index (%)",
        height=420,
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Weights are approximate and drift over time — the fund rebalances "
        "itself; you never have to."
    )

    for name, w, names, strength, weakness in sectors:
        with st.expander(f"{name} (~{w}%) — {names}"):
            st.markdown(
                f"**Strength:** {strength}\n\n**Weakness:** {weakness}"
            )

    st.markdown(
        """
##### The punchline

Sectors take turns winning, and the order is famously unpredictable —
energy went from the worst sector of 2020 to the best of 2022; tech did
roughly the reverse. Professionals routinely fail to guess the rotation.
**That unpredictability is the argument for the fund**: whichever sector
has its year, you're already in it. Understanding the ingredients isn't
an invitation to start picking them — it's the reason you can relax about
owning them all.
"""
    )

# ---------------------------------------------------------------- tab 7

with tab7:
    st.subheader("The boring consensus checklist")
    st.markdown(
        "The quiet fear behind all the others: *am I doing something "
        "wrong?* Here's the thing — for long-term index investors, the "
        "consensus among experienced investors (Bogleheads, r/personalfinance, "
        "and Warren Buffett's advice to his own family) is short, stable, "
        "and boring. Check yourself against it:"
    )

    checks = [
        "I'm only investing money I won't need for roughly 5+ years "
        "(emergency cushion and upcoming bills stay in cash).",
        "I'm buying a broad, low-cost index fund — not individual stocks, "
        "not a hot tip.",
        "I add money when I can. The amount and rhythm don't need to be "
        "perfect or consistent — small and irregular still counts.",
        "I don't plan to sell when the market drops. Down years are part "
        "of the deal, not a signal.",
        "I check occasionally — not daily. (See 'The cost of looking.')",
    ]

    checked = [st.checkbox(c, key=f"chk{i}") for i, c in enumerate(checks)]

    if all(checked):
        st.success(
            "That's the whole system. If you can honestly tick these five "
            "boxes, you are doing what the boring consensus recommends — "
            "there is no hidden step six that experienced people know and "
            "you don't."
        )
    else:
        st.info(
            f"{sum(checked)} of {len(checks)} — tick the ones that describe "
            "your plan. Any box you can't tick yet is the *only* homework "
            "there is."
        )

    st.markdown(
        """
##### What "doing it wrong" actually looks like

The real mistake list is short, and none of it is about timing or amounts:
investing money you'll need soon · picking individual stocks on tips ·
buying things you don't understand · selling in a panic during a drop ·
checking so often that you're tempted into the first four.

##### Why you can trust the consensus

This advice is boring because it has survived every market era, every
crash on the Worst Case tab, and millions of people pressure-testing it.
When the most patient, most experienced voices in investing all give
beginners the same instruction, disagreeing with them isn't independence —
it's just extra risk. You're not out on a limb here. You're standing in
the most crowded, well-lit spot in all of investing.
"""
    )

# ---------------------------------------------------------------- footer

st.divider()
st.markdown(
    """
##### If you take three things away

1. **Only invest money you won't need for at least five years.** Fear is
   rational when the rent money is on the line. Remove that, and the fear
   loses its fuel.
2. **Add what you can, when you can — then look quarterly at most.**
   You've seen the math: looking less means feeling fewer losses that were
   never real.
3. **Starting small still counts.** $50 invested calmly beats $500
   invested anxiously and sold at the first crash.
"""
)
st.caption(
    f"Data: S&P 500 annual total returns {FIRST}-{LAST}, dividends "
    "reinvested (bundled CSV — this app never fetches live data, by "
    "design). Educational only; not financial, investment, or tax advice."
)
