from peewee import fn
from .bot import *
from .helperFuncs import *
from .usageGraphs import build_usage_graph
from .configFiles.usageDataBase import (
    UsageEvent,
    get_source_breakdown,
    get_top_guilds,
)


@bot.tree.command(name="hello")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}!", ephemeral=True
    )


@bot.tree.command(
    name="update_whitelist", description="Only the bot owner may use this command"
)
@commands.is_owner()
@app_commands.check(is_owner)
@app_commands.default_permissions()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    user_or_guild="ID of the user or guild you wish to update the settings for",
    id_type="Specifies if the ID provided is a user ID or guild ID",
    expiration='The epoch time in second for which whitelisted status expires. A value of "-1" will never expire',
)
@app_commands.choices(
    id_type=[
        discord.app_commands.Choice(name="User", value=1),
        discord.app_commands.Choice(name="Guild", value=0),
    ],
)
async def updateWhiteList(
    interaction: discord.Interaction,
    user_or_guild: str,
    id_type: discord.app_commands.Choice[int],
    expiration: int,
) -> None:
    """A command used to update guild or user white list settings in the SQL DB. Only usable by the bot owner"""
    if id_type.name == "User":
        await interaction.response.defer(ephemeral=True, thinking=True)
        username = ""
        try:
            user = await bot.fetch_user(user_or_guild)
            username = user.name
        except discord.NotFound:
            await interaction.followup.send(
                f'Error fetching user name for ID {user_or_guild}:\n"NotFound"',
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                f'Error fetching user name for ID {user_or_guild}:\n"HTTPException"',
                ephemeral=True,
            )
            return
        userSettings = fetch_user_settings(user_or_guild)
        try:
            # if the user is not in the SQL DB
            if not userSettings:
                userSettings = newUserSettings(user_or_guild, username, expiration)
            else:
                userSettings["username"] = username
                userSettings["expiration"] = expiration
            update_user_settings(user_or_guild, userSettings)
        except Exception as e:
            await interaction.followup.send(
                f"Failed to update user_settings table.", ephemeral=True
            )
            return
        await interaction.followup.send(
            f"Whitelist settings updated for <@{user_or_guild}>:\n**New Expiration:**  "
            + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"),
            ephemeral=True,
        )
        return
    elif id_type.name == "Guild":
        await interaction.response.defer(ephemeral=True, thinking=True)
        username = ""
        try:
            guild = await bot.fetch_guild(user_or_guild)
            guildName = guild.name
        except discord.NotFound:
            await interaction.followup.send(
                f'Error fetching guild name for ID {user_or_guild}:\n"NotFound"',
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                f'Error fetching guild name for ID {user_or_guild}:\n"HTTPException"',
                ephemeral=True,
            )
            return
        guildSettings = fetch_guild_settings(user_or_guild)
        # if the guild is not in the SQL DB
        if not guildSettings:
            temp = {
                "guild_id": user_or_guild,
                "guild": {"name": guildName},
                "channel_id": None,
            }
            guildSettings = newGuildSettings(temp)
        try:
            guildSettings["guild_name"] = guildName
            guildSettings["expiration"] = expiration
            update_guild_settings(user_or_guild, guildSettings)
        except Exception as e:
            print(e, interaction)
            await interaction.followup.send(
                f"Failed to write to guildWhiteList file.", ephemeral=True
            )

        await interaction.followup.send(
            f"Whitelist settings updated for {guildName}:\n**New Expiration:**  "
            + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"),
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"Invalid command parameters, action aborted.", ephemeral=True
    )


@updateWhiteList.error
async def UpdateWLError(interaction: discord.Interaction, error):
    await not_owner_error(interaction, error)


@bot.tree.command(
    name="permissions",
    description="Tells the user when their and/or the server's access they used it on expires",
)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def checkPermissions(interaction: discord.Interaction) -> None:
    """Responds to the interaction with the white list status of the user that triggered the interaction
    and if used in a guild also provides the guild's white list status"""
    userSettings = fetch_user_settings(interaction.user.id)
    expMsg = ""
    if 0 in interaction._integration_owners:
        expMsg = "**Guild:** "
        guildSettings = fetch_guild_settings(interaction.guild_id)
        if guildSettings:
            exp = guildSettings.get("expiration")
            expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
        else:
            expMsg += "Not White Listed."
    expMsg += "\n**User:** "
    if userSettings:
        exp = userSettings.get("expiration")
        expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
    else:
        expMsg += "Not White Listed."

    await interaction.response.send_message(
        content=expMsg,
        ephemeral=True,
    )


@bot.tree.command(
    name="set_server_emojis",
    description="Configures the emojis used for ephemerides requested from prediction menus used within this server.",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.default_permissions()
async def setServerEmojis(
    interaction: discord.Interaction,
    white: str = defaultEmojis["White"],
    black: str = defaultEmojis["Black"],
    green: str = defaultEmojis["Green"],
    red: str = defaultEmojis["Red"],
    purple: str = defaultEmojis["Purple"],
    yellow: str = defaultEmojis["Yellow"],
    cyan: str = defaultEmojis["Cyan"],
    blue: str = defaultEmojis["Blue"],
    new: Optional[str] = defaultEmojis["new"],
    waxing_crescent: Optional[str] = defaultEmojis["waxing_crescent"],
    first_quarter: Optional[str] = defaultEmojis["first_quarter"],
    waxing_gibbous: Optional[str] = defaultEmojis["waxing_gibbous"],
    full: Optional[str] = defaultEmojis["full"],
    waning_gibbous: Optional[str] = defaultEmojis["waning_gibbous"],
    third_quarter: Optional[str] = defaultEmojis["third_quarter"],
    waning_crescent: Optional[str] = defaultEmojis["waning_crescent"],
) -> None:
    """Used to set the emojis for the server that the interaction came from"""
    invalidEmojis = []
    for emoji in (
        white,
        black,
        green,
        red,
        purple,
        yellow,
        cyan,
        blue,
        new,
        waxing_crescent,
        first_quarter,
        waxing_gibbous,
        full,
        waning_gibbous,
        third_quarter,
        waning_crescent,
    ):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        guildSettings = fetch_guild_settings(interaction.guild_id)
        if not guildSettings:
            guildSettings = newGuildSettings(interaction)
        guildSettings["emojis"] = {
            "White": white,
            "Black": black,
            "Green": green,
            "Red": red,
            "Purple": purple,
            "Yellow": yellow,
            "Cyan": cyan,
            "Blue": blue,
            "new": new,
            "waxing_crescent": waxing_crescent,
            "first_quarter": first_quarter,
            "waxing_gibbous": waxing_gibbous,
            "full": full,
            "waning_gibbous": waning_gibbous,
            "third_quarter": third_quarter,
            "waning_crescent": waning_crescent,
        }
        emojis = guildSettings["emojis"]
        update_guild_settings(interaction.guild_id, guildSettings)
        await interaction.response.send_message(
            content="**Successfully set server emojis!**"
            f"\n> `White           ` {emojis['White']}"
            f"\n> `Black           ` {emojis['Black']}"
            f"\n> `Green           ` {emojis['Green']}"
            f"\n> `Red             ` {emojis['Red']}"
            f"\n> `Purple          ` {emojis['Purple']}"
            f"\n> `Yellow          ` {emojis['Yellow']}"
            f"\n> `Cyan            ` {emojis['Cyan']}"
            f"\n> `Blue            ` {emojis['Blue']}"
            f"\n> `New Moon        ` {emojis['new']}"
            f"\n> `Waxing Crescent ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter   ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous  ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon       ` {emojis['full']}"
            f"\n> `Waning Gibbous  ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter   ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent ` {emojis['waning_crescent']}",
            ephemeral=True,
        )


@bot.tree.command(
    name="set_personal_emojis",
    description="Configures the emojis used for ephemerides requested from user installable prediction menus.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe()
async def setPersonalEmojis(
    interaction: discord.Interaction,
    white: str = defaultEmojis["White"],
    black: str = defaultEmojis["Black"],
    green: str = defaultEmojis["Green"],
    red: str = defaultEmojis["Red"],
    purple: str = defaultEmojis["Purple"],
    yellow: str = defaultEmojis["Yellow"],
    cyan: str = defaultEmojis["Cyan"],
    blue: str = defaultEmojis["Blue"],
    new: Optional[str] = defaultEmojis["new"],
    waxing_crescent: Optional[str] = defaultEmojis["waxing_crescent"],
    first_quarter: Optional[str] = defaultEmojis["first_quarter"],
    waxing_gibbous: Optional[str] = defaultEmojis["waxing_gibbous"],
    full: Optional[str] = defaultEmojis["full"],
    waning_gibbous: Optional[str] = defaultEmojis["waning_gibbous"],
    third_quarter: Optional[str] = defaultEmojis["third_quarter"],
    waning_crescent: Optional[str] = defaultEmojis["waning_crescent"],
) -> None:
    """Used to set the emojis that will be used for user installable menus
    for the user that triggered the interaction"""
    invalidEmojis = []
    for emoji in (
        white,
        black,
        green,
        red,
        purple,
        yellow,
        cyan,
        blue,
        new,
        waxing_crescent,
        first_quarter,
        waxing_gibbous,
        full,
        waning_gibbous,
        third_quarter,
        waning_crescent,
    ):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        userSettings = fetch_user_settings(interaction.user.id)
        if not userSettings:
            userSettings = newUserSettings(interaction.user.id, interaction.user.name)
        userSettings["emojis"] = {
            "White": white,
            "Black": black,
            "Green": green,
            "Red": red,
            "Purple": purple,
            "Yellow": yellow,
            "Cyan": cyan,
            "Blue": blue,
            "new": new,
            "waxing_crescent": waxing_crescent,
            "first_quarter": first_quarter,
            "waxing_gibbous": waxing_gibbous,
            "full": full,
            "waning_gibbous": waning_gibbous,
            "third_quarter": third_quarter,
            "waning_crescent": waning_crescent,
        }
        emojis = userSettings["emojis"]
        update_user_settings(interaction.user.id, userSettings)
        await interaction.response.send_message(
            content="**Successfully set personal emojis!**"
            f"\n> `White           ` {emojis['White']}"
            f"\n> `Black           ` {emojis['Black']}"
            f"\n> `Green           ` {emojis['Green']}"
            f"\n> `Red             ` {emojis['Red']}"
            f"\n> `Purple          ` {emojis['Purple']}"
            f"\n> `Yellow          ` {emojis['Yellow']}"
            f"\n> `Cyan            ` {emojis['Cyan']}"
            f"\n> `Blue            ` {emojis['Blue']}"
            f"\n> `New Moon        ` {emojis['new']}"
            f"\n> `Waxing Crescent ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter   ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous  ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon       ` {emojis['full']}"
            f"\n> `Waning Gibbous  ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter   ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent ` {emojis['waning_crescent']}",
            ephemeral=True,
        )


@bot.tree.command(
    name="usage_stats",
    description="Owner-only usage overview for a day range",
)
@commands.is_owner()
@app_commands.check(is_owner)
@app_commands.default_permissions()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    last_days_start="Start of range in days ago (0 = today)",
    last_days_end="End of range in days ago (>= start)",
    user="Optional user for a specific breakdown",
    graph="Include a daily usage graph",
)
async def usageStats(
    interaction: discord.Interaction,
    last_days_start: Optional[int] = 0,
    last_days_end: Optional[int] = 7,
    user: Optional[discord.User] = None,
    graph: Optional[bool] = False,
) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    if last_days_start is None:
        last_days_start = 0
    if last_days_end is None:
        last_days_end = 7
    if last_days_start < 0 or last_days_end < 0:
        await interaction.followup.send(
            content="Days ago values must be zero or greater.",
            ephemeral=True,
        )
        return
    if last_days_end < last_days_start:
        last_days_start, last_days_end = last_days_end, last_days_start

    now = int(time.time())
    start_ts = now - int(last_days_end) * 86400
    end_ts = now - int(last_days_start) * 86400

    filters = [UsageEvent.ts.between(start_ts, end_ts)]
    if user is not None:
        filters.append(UsageEvent.user_id == str(user.id))

    total_count = UsageEvent.select().where(*filters).count()
    if total_count == 0:
        await interaction.followup.send(
            content="No usage records found for that time range.",
            ephemeral=True,
        )
        return
    unique_users = (
        UsageEvent.select(UsageEvent.user_id).where(*filters).distinct().count()
    )

    feature_counts = {"scroll": 0, "lunar": 0}
    extra_features = []
    feature_query = (
        UsageEvent.select(
            UsageEvent.feature, fn.COUNT(UsageEvent.id).alias("count")
        )
        .where(*filters)
        .group_by(UsageEvent.feature)
        .order_by(fn.COUNT(UsageEvent.id).desc())
    )
    for row in feature_query:
        if row.feature in feature_counts:
            feature_counts[row.feature] = row.count
        else:
            extra_features.append(f"{row.feature}: {row.count}")
    feature_summary = (
        f"scroll: {feature_counts['scroll']}, lunar: {feature_counts['lunar']}"
    )
    if extra_features:
        feature_summary = f"{feature_summary}, " + ", ".join(extra_features)

    source_counts = get_source_breakdown(
        start_ts, end_ts, user_id=str(user.id) if user is not None else None
    )
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

    action_query = (
        UsageEvent.select(
            UsageEvent.feature,
            UsageEvent.action,
            UsageEvent.context,
            fn.COUNT(UsageEvent.id).alias("count"),
        )
        .where(*filters)
        .group_by(UsageEvent.feature, UsageEvent.action, UsageEvent.context)
        .order_by(fn.COUNT(UsageEvent.id).desc())
        .limit(10)
    )

    lines = [
        "**Usage stats**",
        f"**Range:** {last_days_end}-{last_days_start} days ago (<t:{start_ts}:d> - <t:{end_ts}:d>)",
    ]
    if user is not None:
        lines.append(f"**User:** {user.mention} ({user.id})")
    lines.append(f"**Total events:** {total_count}")
    lines.append(f"**Unique users:** {unique_users}")
    lines.append(f"**By feature:** {feature_summary}")
    lines.append(
        f"**By install:** {scroll_source_summary}, {lunar_source_summary}"
    )
    top_guilds = get_top_guilds(
        start_ts, end_ts, user_id=str(user.id) if user is not None else None, limit=5
    )
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

    if user is None:
        top_users = (
            UsageEvent.select(
                UsageEvent.user_id,
                UsageEvent.username,
                fn.COUNT(UsageEvent.id).alias("count"),
            )
            .where(UsageEvent.ts.between(start_ts, end_ts))
            .group_by(UsageEvent.user_id, UsageEvent.username)
            .order_by(fn.COUNT(UsageEvent.id).desc())
            .limit(10)
        )
        lines.append("**Top users:**")
        for row in top_users:
            lines.append(f"- {row.username} ({row.user_id}): {row.count}")

    lines.append("**Top actions:**")
    for row in action_query:
        label = f"{row.feature}/{row.action}"
        if row.context:
            label = f"{label} ({row.context})"
        lines.append(f"- {label}: {row.count}")

    message = "\n".join(lines)
    graph_file = None
    if graph:
        buf, error = build_usage_graph(
            start_ts=start_ts,
            end_ts=end_ts,
            user_id=str(user.id) if user is not None else None,
            user_name=user.name if user is not None else None,
        )
        if error:
            await interaction.followup.send(
                content=error,
                ephemeral=True,
            )
        else:
            graph_file = discord.File(fp=buf, filename="usage_stats.png")

    chunks = splitMsg(message)
    if graph_file is not None:
        await interaction.followup.send(
            content=chunks[0], file=graph_file, ephemeral=True
        )
        for chunk in chunks[1:]:
            await interaction.followup.send(content=chunk, ephemeral=True)
    else:
        for chunk in chunks:
            await interaction.followup.send(content=chunk, ephemeral=True)


@usageStats.error
async def usageStatsError(interaction: discord.Interaction, error):
    await not_owner_error(interaction, error)
