"""Charts for the README, drawn from everything in the research cache.

    python -m hiddencity charts      # writes PNGs to docs/charts/
"""

from collections import defaultdict

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt  # noqa: E402

from hiddencity import airports, config, detect  # noqa: E402

CHART_DIR = config.ROOT / "docs" / "charts"

# Colours from the site: one series per chart, so one hue (validated against the surface).
MARK = "#177a52"
SURFACE = "#fffdf8"
INK = "#14211b"
MUTED = "#5b675f"
GRID = "#e2ddcf"


def style(ax, title, subtitle):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=10)
    ax.figure.text(0.02, 0.95, title, fontsize=14, fontweight="bold", color=INK, ha="left", va="top")
    ax.figure.text(0.02, 0.89, subtitle, fontsize=10, color=MUTED, ha="left", va="top")


def save(fig, name):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def best_connection_per_route(rows):
    """{(origin, hub, date): cheapest connecting ticket whose first stop is the hub}."""
    best = {}
    for row in rows:
        if row["stops"] == 0 or row["first_stop"] == row["final_destination"]:
            continue
        key = (row["origin"], row["first_stop"], row["date"])
        if key not in best or row["price"] < best[key]:
            best[key] = row["price"]
    return best


def chart_by_date(rows, opportunities):
    direct = detect.cheapest_direct_prices(rows)
    checked = defaultdict(int)
    with_saving = defaultdict(set)
    for origin, hub, date in direct:
        checked[date] += 1
    for opp in opportunities:
        with_saving[opp["date"]].add(opp["hub"])

    dates = sorted(checked)
    shares = [100 * len(with_saving[d]) / checked[d] for d in dates]
    labels = []
    for d in dates:
        _, month, day = d.split("-")
        weekday = __import__("datetime").date.fromisoformat(d).strftime("%a")
        labels.append(f"{weekday}\n{int(day)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(month) - 1]}")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    fig.subplots_adjust(top=0.78, bottom=0.16, left=0.06, right=0.98)
    bars = ax.bar(labels, shares, width=0.5, color=MARK)
    for bar, d, share in zip(bars, dates, shares):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            f"{share:.0f}%  ({len(with_saving[d])}/{checked[d]})",
            ha="center", va="bottom", fontsize=10, color=INK,
        )
    ax.set_yticks([])
    ax.set_ylim(0, max(shares + [1]) * 1.3)
    style(ax, "Hidden-city savings by travel date",
          "Share of Delhi → city routes where a longer ticket was cheaper than flying direct")
    return save(fig, "savings_by_date.png")


def chart_by_hub(opportunities):
    best = {}
    for opp in opportunities:
        best[opp["hub"]] = max(best.get(opp["hub"], 0), opp["saving"])
    hubs = sorted(best, key=best.get)[-12:]  # the 12 biggest, smallest at the bottom
    names = [f"{airports.city(h)} ({h})" if h in airports.AIRPORTS else h for h in hubs]
    values = [best[h] for h in hubs]

    fig, ax = plt.subplots(figsize=(8, 0.42 * len(hubs) + 1.6))
    fig.subplots_adjust(top=1 - 1.1 / (0.42 * len(hubs) + 1.6), bottom=0.06, left=0.3, right=0.9)
    ax.barh(names, values, height=0.55, color=MARK)
    for y, v in enumerate(values):
        ax.text(v + max(values) * 0.01, y, f"₹{v:,}", va="center", fontsize=10, color=INK)
    ax.set_xticks([])
    ax.set_xlim(0, max(values) * 1.15)
    style(ax, "Biggest saving at each stopover city",
          "Best single hidden-city fare found, across all scanned dates")
    return save(fig, "best_saving_by_city.png")


def chart_how_close(rows):
    direct = detect.cheapest_direct_prices(rows)
    best = best_connection_per_route(rows)
    ratios = [100 * best[k] / direct[k] for k in best if k in direct]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    fig.subplots_adjust(top=0.78, bottom=0.16, left=0.06, right=0.98)
    bins = list(range(40, 260, 10))
    clipped = [min(max(r, 40), 259) for r in ratios]
    ax.hist(clipped, bins=bins, color=MARK, rwidth=0.85)
    ax.axvline(100, color=INK, linewidth=1.5)
    cheaper = sum(1 for r in ratios if r < 100)
    ax.text(98, ax.get_ylim()[1] * 0.95, f"cheaper than direct ←\n{cheaper} of {len(ratios)} routes",
            ha="right", va="top", fontsize=10, color=INK)
    dearer = len(ratios) - cheaper
    ax.text(250, ax.get_ylim()[1] * 0.95, f"→ dearer than direct\n{dearer} of {len(ratios)} routes",
            ha="right", va="top", fontsize=10, color=INK)
    ax.set_xlabel("Cheapest hidden-city ticket as % of the cheapest direct fare", color=MUTED)
    ax.set_yticks([])
    style(ax, "Most connections cost more than flying direct",
          "Every Delhi → stopover route and date with both a direct fare and a connection through it")
    return save(fig, "how_close_connections_get.png")


def make_all(rows, opportunities):
    paths = [chart_by_date(rows, opportunities), chart_how_close(rows)]
    if opportunities:
        paths.append(chart_by_hub(opportunities))
    return paths
