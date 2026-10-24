"""Figure 1: Star Bulk's share price against its own capital actions, today's NAV range and the trade levels."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs" / "pair_results.json"
INK, MUTED, RULE, ACCENT, BUY, SELL = "#1B1F24", "#5B6470", "#D9DDE3", "#1F4E79", "#2E7D5B", "#B5523B"

px = pd.read_csv(ROOT / "data" / "prices.csv", parse_dates=["date"])
close = px[px.ticker == "SBLK"].set_index("date").close.loc["2025-01-01":"2026-10-23"]
s = json.loads(RESULTS.read_text())["SBLK"]
nav = {c: s[c]["nav_per_share"] for c in ("bear", "base", "bull")}

plt.rcParams.update({"font.family": "Helvetica", "font.size": 7})
fig, ax = plt.subplots(figsize=(7.1, 2.2), dpi=300)

# Disclosed buybacks (cash-flow statements): Q1 2026 $37.9m, Q2 2026 $8.4m (H1 $46.3m less Q1)
for (a, b, label, y, alpha) in [("2026-01-01", "2026-03-31", "Q1 26 buybacks\n$37.9m", 39.6, 0.16),
                                ("2026-04-01", "2026-06-30", "Q2 26 buybacks\n$8.4m", 36.2, 0.08)]:
    ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=BUY, alpha=alpha, lw=0)
    ax.text(pd.Timestamp(a) + pd.Timedelta(days=4), y, label, color=BUY, fontsize=6.7, va="top")

ax.plot(close.index, close.values, color=ACCENT, lw=1.1)

# Athens issue: 4.4m new shares at EUR 24.50 (about $28.45), closed 11 Sep 2026
issue = pd.Timestamp("2026-09-11")
ax.scatter([issue], [28.45], s=22, color=SELL, zorder=5)
ax.annotate("Athens issue: 4.4m new shares\nat ~$28.45 (0.86x NAV)", (issue, 28.45),
            xytext=(pd.Timestamp("2026-06-25"), 17.0), textcoords="data", fontsize=6.7, color=SELL,
            arrowprops={"arrowstyle": "-", "color": SELL, "lw": 0.6})

# Right edge: today's price, scenario NAVs and trade levels (dated October 2026 estimates, not history)
end = close.index[-1]
x0, x1 = end + pd.Timedelta(days=50), end + pd.Timedelta(days=100)
ax.fill_between([x0, x1], nav["bear"], nav["bull"], color=RULE, lw=0)
for v, label, col, w in [(nav["bull"], f"Bull NAV ${nav['bull']:.2f}", MUTED, 0.6),
                         (nav["base"], f"Base NAV ${nav['base']:.2f}  trim", INK, 1.0),
                         (0.8 * nav["base"], f"0.80x NAV ${0.8 * nav['base']:.2f}  add", BUY, 0.8),
                         (nav["bear"], f"Bear NAV ${nav['bear']:.2f}", MUTED, 0.6)]:
    ax.plot([x0, x1], [v, v], color=col, lw=w)
    ax.text(x1 + pd.Timedelta(days=4), v, label, color=col, fontsize=6.7, va="center")
ax.scatter([end], [close.iloc[-1]], s=16, color=ACCENT, zorder=5)
ax.text(end + pd.Timedelta(days=6), close.iloc[-1], f"${close.iloc[-1]:.2f}\n23 Oct", color=ACCENT,
        fontsize=6.7, ha="left", va="center")

ax.set_xlim(close.index[0], end + pd.Timedelta(days=215))
ax.set_ylim(10, 41)
ax.set_ylabel("USD per share", color=MUTED, fontsize=6.8)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
for sp in ["left", "bottom"]:
    ax.spines[sp].set_color(MUTED)
ax.tick_params(colors=MUTED, labelsize=6.7)
ax.set_xticks(pd.date_range("2025-01-01", "2026-10-01", freq="3MS"))
ax.set_xticklabels([d.strftime("%b %y") for d in pd.date_range("2025-01-01", "2026-10-01", freq="3MS")])
fig.tight_layout(pad=0.3)
out = ROOT / "thesis" / "fig_stewardship.png"
fig.savefig(out)
print("wrote", out)
