import time
from peewee import fn
from discord.ext import tasks
from .guildScrollMenus import *
from .guildLunarMenus import *
from .helperFuncs import splitMsg
from .configFiles.usageDataBase import (
    UsageEvent,
    get_source_breakdown,
    get_top_guilds,
)
from .configFiles.variables import (
    ENABLE_USAGE_LOGGING,
    ENABLE_USAGE_REPORTS,
    USAGE_REPORT_INTERVAL_HOURS,
    USAGE_REPORT_CHANNEL_ID,
    ownerID,
)

REPORT_INTERVAL_HOURS = (
    USAGE_REPORT_INTERVAL_HOURS if USAGE_REPORT_INTERVAL_HOURS > 0 else 24
)


# allows for menus to persist and continue working between bot restarts
class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix="~", intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(GuildScrollMenu(allow_filters=1, setUp=False))
        self.add_view(GuildLunarMenu())


bot = PersistentViewBot()


@bot.event
async def on_ready():
    print("Bot is up and ready!")
    try:
        synched = await bot.tree.sync()
        print(f"synched {len(synched)} command(s)")
    except Exception as e:
        print(e)
    if (
        ENABLE_USAGE_REPORTS
        and ENABLE_USAGE_LOGGING
        and USAGE_REPORT_INTERVAL_HOURS > 0
        and not usage_report_task.is_running()
    ):
        usage_report_task.start()


def _format_usage_report(range_label: str, start_ts: int, end_ts: int) -> list[str]:
    filters = [UsageEvent.ts.between(start_ts, end_ts)]
    total_count = UsageEvent.select().where(*filters).count()
    unique_users = (
        UsageEvent.select(UsageEvent.user_id).where(*filters).distinct().count()
    )
    source_counts = get_source_breakdown(start_ts, end_ts)
    scroll_sources = source_counts.get(
        "scroll", {"guild": 0, "user_install": 0, "unknown": 0}
    )
    lunar_sources = source_counts.get(
        "lunar", {"guild": 0, "user_install": 0, "unknown": 0}
    )
    scroll_source_summary = (
        f"scroll (guild {scroll_sources['guild']}, user {scroll_sources['user_install']}"
    )
    if scroll_sources["unknown"] > 0:
        scroll_source_summary += f", unknown {scroll_sources['unknown']}"
    scroll_source_summary += ")"
    lunar_source_summary = (
        f"lunar (guild {lunar_sources['guild']}, user {lunar_sources['user_install']}"
    )
    if lunar_sources["unknown"] > 0:
        lunar_source_summary += f", unknown {lunar_sources['unknown']}"
    lunar_source_summary += ")"
    feature_query = (
        UsageEvent.select(
            UsageEvent.feature, fn.COUNT(UsageEvent.id).alias("count")
        )
        .where(*filters)
        .group_by(UsageEvent.feature)
        .order_by(fn.COUNT(UsageEvent.id).desc())
    )
    feature_parts = []
    for row in feature_query:
        feature_parts.append(f"{row.feature}: {row.count}")
    feature_summary = ", ".join(feature_parts) if feature_parts else "none"
    top_users = (
        UsageEvent.select(
            UsageEvent.username,
            UsageEvent.user_id,
            fn.COUNT(UsageEvent.id).alias("count"),
        )
        .where(*filters)
        .group_by(UsageEvent.user_id, UsageEvent.username)
        .order_by(fn.COUNT(UsageEvent.id).desc())
        .limit(5)
    )
    lines = [
        f"**{range_label}** (<t:{start_ts}:d> - <t:{end_ts}:d>)",
        f"**Total events:** {total_count}",
        f"**Unique users:** {unique_users}",
        f"**By feature:** {feature_summary}",
        f"**By install:** {scroll_source_summary}, {lunar_source_summary}",
    ]
    top_guilds = get_top_guilds(start_ts, end_ts, limit=5)
    if top_guilds:
        lines.append("**Top guilds:**")
        for guild_id, count in top_guilds:
            guild_obj = bot.get_guild(int(guild_id))
            if guild_obj is not None:
                label = f"{guild_obj.name} ({guild_id})"
            else:
                label = f"{guild_id}"
            lines.append(f"- {label}: {count}")
    else:
        lines.append("**Top guilds:** none")
    if total_count > 0:
        lines.append("**Top users:**")
        for row in top_users:
            lines.append(f"- {row.username} ({row.user_id}): {row.count}")
    return lines


@tasks.loop(hours=REPORT_INTERVAL_HOURS)
async def usage_report_task():
    if not ENABLE_USAGE_REPORTS or not ENABLE_USAGE_LOGGING:
        return
    try:
        now = int(time.time())
        daily_start = now - 86400
        weekly_start = now - 7 * 86400
        lines = [
            "**Usage stats (automated)**",
            f"**Interval:** every {REPORT_INTERVAL_HOURS} hours",
            "",
        ]
        lines.extend(_format_usage_report("Daily (last 24h)", daily_start, now))
        lines.append("")
        lines.extend(_format_usage_report("Weekly (last 7d)", weekly_start, now))
        message = "\n".join(lines)

        if USAGE_REPORT_CHANNEL_ID is not None:
            channel = bot.get_channel(int(USAGE_REPORT_CHANNEL_ID))
            if channel is None:
                channel = await bot.fetch_channel(int(USAGE_REPORT_CHANNEL_ID))
            for chunk in splitMsg(message):
                await channel.send(chunk)
            return

        owner = await bot.fetch_user(ownerID)
        for chunk in splitMsg(message):
            await owner.send(chunk)
    except Exception as e:
        print(f"Usage report task error: {e}")


@usage_report_task.before_loop
async def usage_report_task_before_loop():
    await bot.wait_until_ready()
