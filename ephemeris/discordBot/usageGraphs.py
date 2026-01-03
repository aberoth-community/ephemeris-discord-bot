import io
from datetime import datetime
from typing import Optional, Tuple

from .configFiles.usageDataBase import UsageEvent


def _build_daily_series(
    start_ts: int, end_ts: int, user_id: Optional[str]
) -> Tuple[list[datetime], list[int], list[int], list[int], list[int]]:
    num_days = int((end_ts - start_ts) // 86400)
    if num_days <= 0:
        return [], [], [], [], []
    totals = [0] * num_days
    scroll_counts = [0] * num_days
    lunar_counts = [0] * num_days
    user_sets = [set() for _ in range(num_days)]

    query = UsageEvent.select(
        UsageEvent.ts, UsageEvent.feature, UsageEvent.user_id
    ).where(UsageEvent.ts.between(start_ts, end_ts))
    if user_id is not None:
        query = query.where(UsageEvent.user_id == str(user_id))

    for row in query:
        idx = int((row.ts - start_ts) // 86400)
        if idx == num_days:
            idx = num_days - 1
        if idx < 0 or idx >= num_days:
            continue
        totals[idx] += 1
        if row.feature == "scroll":
            scroll_counts[idx] += 1
        elif row.feature == "lunar":
            lunar_counts[idx] += 1
        user_sets[idx].add(row.user_id)

    labels = []
    for i in range(num_days):
        day_start = start_ts + (i * 86400)
        labels.append(datetime.utcfromtimestamp(day_start))
    unique_counts = [len(s) for s in user_sets]
    return labels, totals, scroll_counts, lunar_counts, unique_counts


def build_usage_graph(
    start_ts: int,
    end_ts: int,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib import patheffects
    except Exception as exc:
        return None, "Graphing requires matplotlib to be installed."

    labels, totals, scroll_counts, lunar_counts, unique_counts = _build_daily_series(
        start_ts, end_ts, user_id
    )
    if not labels:
        return None, "Graphing requires a range of at least 1 day."

    if sum(totals) == 0:
        show_data = False
    else:
        show_data = True

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#40444B")
    ax.set_facecolor("#40444B")

    axes_xcolor = "#E9E9E9"
    spine_color = "#1B1C1F"
    grid_color = "#2C2E33"

    ax.plot(labels, totals, color="#FAC32D", marker="o", label="Total", linewidth=2)
    ax.plot(
        labels,
        scroll_counts,
        color="#0BB150",
        marker="o",
        label="Scroll",
        linewidth=2,
    )
    ax.plot(
        labels,
        lunar_counts,
        color="#5B6CFF",
        marker="o",
        label="Lunar",
        linewidth=2,
    )
    if user_id is None:
        ax.plot(
            labels,
            unique_counts,
            color="#B3B9FF",
            marker="o",
            label="Unique users",
            linewidth=2,
            linestyle="--",
        )

    title = "Usage over time"
    if user_name:
        title = f"Usage over time - {user_name}"
    title_obj = ax.set_title(title, color=axes_xcolor, fontsize=14)
    title_obj.set_path_effects(
        [patheffects.withStroke(linewidth=3, foreground=spine_color)]
    )

    ax.set_xlabel("Date (UTC)", color=axes_xcolor)
    ax.set_ylabel("Events", color=axes_xcolor)
    ax.grid(color=grid_color)
    ax.tick_params(axis="x", colors=axes_xcolor)
    ax.tick_params(axis="y", colors=axes_xcolor)

    for spine in ax.spines.values():
        spine.set_color(spine_color)
        spine.set_linewidth(2)

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
        tick.set_ha("right")

    legend = ax.legend()
    if legend is not None:
        legend.get_frame().set_facecolor("#40444B")
        legend.get_frame().set_edgecolor(spine_color)
        for text in legend.get_texts():
            text.set_color(axes_xcolor)

    if not show_data:
        props = dict(boxstyle="round", facecolor="ivory", alpha=0.7)
        ax.text(
            0.5,
            0.5,
            "Not Enough Data!",
            transform=ax.transAxes,
            fontsize=18,
            va="center",
            ha="center",
            bbox=props,
        )
        ax.set_yticks([])
        ax.set_xticks([])

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf, None
