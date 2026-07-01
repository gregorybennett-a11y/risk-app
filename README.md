# 🌿 Steady

A calm web app for people who are afraid of losing money in the stock market.

Built on real S&P 500 total returns from 2000–2025 (dividends reinvested) —
the market you've actually lived through. No live prices, no ticking
numbers — by design. The app exists to prove one thing: for a long-term
index investor, checking less and holding longer has historically been the
winning move.

## The six tabs

1. **🌱 Start small** — pick an amount and a rough rhythm (monthly,
   quarterly, whenever) and see the outcome of every possible starting
   year since 2000.
2. **⏳ Fast forward** — your amount rides every real 5-20 year stretch
   of the modern market, overlaid, so you see the shape of the ride ahead
   (history's roads, not a forecast).
3. **👀 The cost of looking** — same investment, same decade: how much
   "losing" you experience depends only on how often you check.
4. **🌧️ Worst case** — deliberately invest right before the dot-com bust,
   the 2008 crisis, or the 2022 bear, and watch the recovery.
5. **🧺 What's inside the fund** — the 11 sectors of the US market, each
   one's strengths and weaknesses, and why owning all of them beats
   guessing.
6. **✅ Am I doing this right?** — the boring consensus checklist, and the
   short list of actual mistakes.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**.
3. Pick the repo, branch `main`, main file `app.py`. Deploy.

## Data

`data/sp500_annual_total_returns.csv` — S&P 500 annual total returns
(price + reinvested dividends). The app uses 2000 onward. Bundled
statically so the app is fast, free to host, and never breaks.

*Educational only — not financial advice.*
