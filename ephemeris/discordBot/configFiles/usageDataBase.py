import json
import time
from typing import Optional
from peewee import Model, SqliteDatabase, CharField, IntegerField, TextField, fn

# Connect to the SQLite database for usage tracking
usage_db = SqliteDatabase("ephemeris\\discordBot\\configFiles\\usage_DB.db")


class BaseModel(Model):
    class Meta:
        database = usage_db


class UsageEvent(BaseModel):
    ts = IntegerField(index=True)
    user_id = CharField(index=True)
    username = CharField()
    guild_id = CharField(null=True)
    channel_id = CharField(null=True)
    feature = CharField(index=True)
    action = CharField(index=True)
    context = TextField(null=True)
    details = TextField(null=True)


# Create table
usage_db.connect()
usage_db.create_tables([UsageEvent])


def log_usage_event(
    interaction,
    feature: str,
    action: str,
    context: Optional[str] = None,
    details=None,
):
    details_text = None
    if details is not None:
        if isinstance(details, str):
            details_text = details
        else:
            details_text = json.dumps(details)
    UsageEvent.create(
        ts=int(time.time()),
        user_id=str(interaction.user.id),
        username=interaction.user.name,
        guild_id=str(interaction.guild_id) if interaction.guild_id else None,
        channel_id=str(interaction.channel_id) if interaction.channel_id else None,
        feature=feature,
        action=action,
        context=context,
        details=details_text,
    )


def _extract_source(context: Optional[str], details_text: Optional[str]) -> str:
    if details_text:
        try:
            details = json.loads(details_text)
            if isinstance(details, dict):
                source = details.get("source")
                if source:
                    return source
        except json.JSONDecodeError:
            pass
    if context in ("guild", "user_install"):
        return context
    return "unknown"


def get_source_breakdown(start_ts: int, end_ts: int, user_id: Optional[str] = None):
    query = UsageEvent.select(
        UsageEvent.feature,
        UsageEvent.context,
        UsageEvent.details,
    ).where(UsageEvent.ts.between(start_ts, end_ts))
    if user_id is not None:
        query = query.where(UsageEvent.user_id == str(user_id))
    counts = {}
    for row in query:
        feature = row.feature or "unknown"
        if feature not in counts:
            counts[feature] = {"guild": 0, "user_install": 0, "unknown": 0}
        source = _extract_source(row.context, row.details)
        if source not in counts[feature]:
            counts[feature][source] = 0
        counts[feature][source] += 1
    return counts


def get_top_guild(start_ts: int, end_ts: int, user_id: Optional[str] = None):
    rows = get_top_guilds(start_ts, end_ts, user_id=user_id, limit=1)
    if not rows:
        return None, 0
    return rows[0]


def get_top_guilds(
    start_ts: int,
    end_ts: int,
    user_id: Optional[str] = None,
    limit: int = 5,
):
    query = (
        UsageEvent.select(
            UsageEvent.guild_id, fn.COUNT(UsageEvent.id).alias("count")
        )
        .where(
            UsageEvent.ts.between(start_ts, end_ts),
            UsageEvent.guild_id.is_null(False),
        )
        .group_by(UsageEvent.guild_id)
        .order_by(fn.COUNT(UsageEvent.id).desc())
        .limit(limit)
    )
    if user_id is not None:
        query = query.where(UsageEvent.user_id == str(user_id))
    return [(row.guild_id, row.count) for row in query]
