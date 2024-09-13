from .bot import bot
from .guildScrollMenus import *
from .guildLunarMenus import *
from .helperFuncs import *

@bot.tree.command(
    name="create_persistent_scroll_menu",
    description="Creates prediction menu with no timeout. Requires admin. All users will be able to use interface.",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.default_permissions()
@app_commands.describe(
    use_emojis="Whether or not responses use emojis for orb names",
    allow_filters="Enables Filtering by orb. Filter settings are shared between all users",
)
@app_commands.choices(
    use_emojis=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
    allow_filters=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
    whitelisted_users_only=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
)
async def guildScrollMenu(
    interaction: discord.Interaction,
    use_emojis: discord.app_commands.Choice[int],
    allow_filters: discord.app_commands.Choice[int],
    whitelisted_users_only: discord.app_commands.Choice[int]
):
    ephRes = True
    noPermission = False
    exp = 0
    if str(interaction.guild_id) not in guildWhiteList:
        noPermission = True
    else: exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
    if (exp != None and exp < time.time() and exp != -1):
        noPermission = True
    if noPermission and not disableWhitelisting:
        await interaction.response.send_message(
            content="**Server does not have permission to use this command.**\nType `/permsissions` for more information.",
            ephemeral=True,
        )
        return
    if str(interaction.guild_id) in guildSettings:
        guildSettings[str(interaction.guild_id)][str(interaction.channel_id)] = {
            "useEmojis": use_emojis.value,
            "allow_filters": allow_filters.value,
            "whitelisted_users_only": whitelisted_users_only.value
        }
    else:
        guildSettings[str(interaction.guild_id)] = {
            str(interaction.channel_id): {
                "useEmojis": use_emojis.value,
                "allow_filters": allow_filters.value,
                "whitelisted_users_only": whitelisted_users_only.value
            }
        }
    updateSettings(settings=guildSettings)
    if (
        use_emojis.value == 1
        and "emojis" not in guildSettings[str(interaction.guild_id)]
    ):
        await interaction.response.send_message(
            content="**Please configure the server emoji settings (/set_server_emojis) to use this command __with emojis.__**",
            ephemeral=True,
        )
        return
    embed = discord.Embed(
        title="**Select what day you would like the scroll events for**",
        description="*Glows should be accurate within a minute*",
        color=0xA21613,
    )
    embed.add_field(
        name="**__Details:__**",
        value="​\n**`Yesterday:`**\n```Returns all scroll events between now and 24 hours ago.```"
        "\n**`Today:    `**\n```Returns all scroll events between 6 hours ago and 24 hours from now.```"
        "\n**`Tomorrow: `**\n```Returns all scroll events between 24 hours from now to 48 hours from now.```"
        "\n**`Later:    `**\n```Use the drop down menu to select a range of days relative to now you'd like the scroll events for."
        "\nIf only one day is selected events for that day will be given```"
        "\n***Note:** Due to daily auto-calibration, predictions may improve in accuracy when requested closer to the date that they occur on.*",
        inline=False,
    )
    embed.set_thumbnail(url=scrollThumbnailURL)
    await interaction.response.send_message(
        embed=embed, view=GuildScrollMenu(allow_filters=allow_filters.value), ephemeral=False
    )


@bot.tree.command(
    name="create_persistent_lunar_calendar",
    description="Creates lunar calendar menu with no timeout. Requires admin. Menu usable by all users",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.default_permissions()
@app_commands.describe(
    user_set_emojis="Whether or not responses use default or user set emojis for moon phase icons",
)
@app_commands.choices(
    user_set_emojis=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
    whitelisted_users_only=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
)
async def guildLunarMenu(
    interaction: discord.Interaction,
    user_set_emojis: discord.app_commands.Choice[int],
    whitelisted_users_only: discord.app_commands.Choice[int]
):
    ephRes = True
    noPermission = False
    exp = 0
    if str(interaction.guild_id) not in guildWhiteList:
        noPermission = True
    else: exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
    if (exp != None and exp < time.time() and exp != -1):
        noPermission = True
    if noPermission and not disableWhitelisting:
        await interaction.response.send_message(
            content="**Server does not have permission to use this command.**\nType `/permsissions` for more information.",
            ephemeral=True,
        )
        return
    if str(interaction.guild_id) in guildSettings:
        guildSettings[str(interaction.guild_id)][str(interaction.channel_id)] = {
            "useEmojis": user_set_emojis.value,
            "whitelisted_users_only": whitelisted_users_only.value
        }
    else:
        guildSettings[str(interaction.guild_id)] = {
            str(interaction.channel_id): {
                "useEmojis": user_set_emojis.value,
                "whitelisted_users_only": whitelisted_users_only.value
            }
        }
    updateSettings(settings=guildSettings)
    if (
        user_set_emojis.value == 1
        and "emojis" not in guildSettings[str(interaction.guild_id)]
    ):
        await interaction.response.send_message(
            content="**Please configure the server emoji settings (/set_server_emojis) to use this command __with emojis.__**",
            ephemeral=True,
        )
        return
    embed = discord.Embed(
        title="**Lunar Calendar**",
        description="Night will start 42 minutes after the start of each moon phase",
        color=0xbcc7cf,
    )
    embed.add_field(
        name="",
        value=f"​\n{defaultEmojis['lunation']}  **All Moons:**\n```Provides a list with the times at which each phase starts for the next {numDisplayMoonCycles} syndonic aberoth months```"
                f"\n{defaultEmojis['full']}  **Next Full Moon:**\n```Provides the time at which the next full moon will start.```"
                f"\n{defaultEmojis['new']}  **Next New Moon:**\n```Provides the time at which the next new moon will start.```"
                f"\n:grey_question:   **Current Phase:**\n```Provides the current phase.```"
                "\n:mag:  **Filter:**\n```Use the drop down menu to select one or more moon phases."
                f" Creates list with the times at which the selected phases start for the next {numFilterDisplayMoonCycles} syndonic aberoth months will be provided```",
        inline=False,
    )
    embed.set_thumbnail(url=moonThumbnailURL)
    await interaction.response.send_message(
        embed=embed, view=GuildLunarMenu(), ephemeral=False
    )
