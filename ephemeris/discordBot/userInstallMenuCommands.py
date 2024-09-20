from .bot import *
from .userInstallScrollMenus import *
from .userInstallLunarMenus import *
from .helperFuncs import *


@bot.tree.command(
    name="prediction_menu",
    description="Creates predictions menu for glows and darks. Has a timeout.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    use_emojis="Whether or not responses use emojis for orb names",
    whitelist_only='Setting to "Yes" will only allow users who\'ve been whitelisted to interact with the menu',
)
@app_commands.choices(
    use_emojis=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
    whitelist_only=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
)
async def userInstallScrollMenu(
    interaction: discord.Interaction,
    use_emojis: discord.app_commands.Choice[int],
    whitelist_only: Optional[discord.app_commands.Choice[int]] = 0,
) -> None:
    """A command that spawns a user install scroll prediction menu"""
    userSettings = fetch_user_settings(interaction.user.id)
    ephRes = False
    whiteListed = False
    if userSettings:
        exp = userSettings.get("expiration")
        whiteListed = True if exp == -1 else exp > time.time()
    else:
        userSettings = newUserSettings(interaction.user.id, interaction.user.name)
        update_user_settings(interaction.user.id, userSettings)
    if not whiteListed and not disableWhitelisting:
        await interaction.response.send_message(
            content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
            ephemeral=True,
        )
        return

    if use_emojis.value == 1 and not userSettings["emojis"]:
        await interaction.response.send_message(
            content="**Please configure your personal emoji settings (/set_personal_emojis) to use this command __with emojis.__**"
            "\nNote: the default options for `/set_personal_emojis` require the user to have nitro and be in the server the emojis are from.",
            ephemeral=True,
        )
        return
    embed = discord.Embed(
        title="**Select what day you would like the scroll events for**",
        description="*Glows should be accurate within a minute*",
        color=0xA21613,
    )
    embed.add_field(
        name="**__Options:__**",
        value="​\n**`Yesterday:`**\n```Returns all scroll events between now and 24 hours ago.```"
        "\n**`Today:    `**\n```Returns all scroll events between 6 hours ago and 24 hours from now.```"
        "\n**`Tomorrow: `**\n```Returns all scroll events between 24 hours from now to 48 hours from now.```"
        "\n**`Later:    `**\n```Use the drop down menu to select what day from now you'd like the scroll events for.```"
        "\n***Note:** Due to automatic calibrations, predictions may improve in accuracy when requested closer to the date that they occur on.*",
        inline=False,
    )
    embed.set_thumbnail(url=scrollThumbnailURL)
    embed.set_footer(text="⏱️ Menu expires in five minutes")

    whitelist_only = whitelist_only.value if whitelist_only else 0
    await interaction.response.send_message(
        embed=embed,
        view=UserInstallScrollMenu(
            useEmojis=True if use_emojis.value == 1 else False,
            whiteListOnly=True if whitelist_only == 1 else False,
            emojis=None if use_emojis.value == 0 else userSettings["emojis"],
        ),
        ephemeral=False,
    )


@bot.tree.command(
    name="lunar_calendar",
    description="Creates lunar calendar menu. Has a timeout",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    user_set_emojis="Whether or not responses use default or user set emojis for moon phase icons",
    whitelisted_users_only="Whether or not this menu requires other users to also be white listed to use",
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
async def userInstallLunarMenu(
    interaction: discord.Interaction,
    user_set_emojis: discord.app_commands.Choice[int],
    whitelisted_users_only: Optional[discord.app_commands.Choice[int]] = 0,
) -> None:
    """A command that spawns a user installable lunar calendar menu"""
    userSettings = fetch_user_settings(interaction.user.id)
    ephRes = False
    whiteListed = False
    if userSettings:
        exp = userSettings.get("expiration")
        whiteListed = True if exp == -1 else exp > time.time()
    else:
        userSettings = newUserSettings(interaction.user.id, interaction.user.name)
        update_user_settings(interaction.user.id, userSettings)
    if not whiteListed and not disableWhitelisting:
        await interaction.response.send_message(
            content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
            ephemeral=True,
        )
        return

    if user_set_emojis.value == 1 and not userSettings["emojis"]:
        await interaction.response.send_message(
            content="**Please configure your personal emoji settings (/set_personal_emojis) to use this command __with emojis.__**"
            "\nNote: the default options for `/set_personal_emojis` require the user to have nitro and be in the server the emojis are from.",
            ephemeral=True,
        )
        return
    embed = discord.Embed(
        title="**Lunar Calendar**",
        description="Night will start 42 minutes after the start of each moon phase",
        color=0xBCC7CF,
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
    embed.set_footer(text="⏱️ Menu expires in five minutes")
    whitelisted_users_only = (
        whitelisted_users_only.value if whitelisted_users_only else 0
    )
    await interaction.response.send_message(
        embed=embed,
        view=UserInstallLunarMenu(
            useEmojis=True if user_set_emojis.value == 1 else False,
            whiteListUsersOnly=True if whitelisted_users_only == 1 else False,
            emojis=None if user_set_emojis.value == 0 else userSettings["emojis"],
        ),
        ephemeral=False,
    )
