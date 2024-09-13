from .bot import *
from .userInstallScrollMenus import *
from .userInstallLunarMenus import *
from .helperFuncs import *

@bot.tree.command(
    name="prediction_menu",
    description="Creates predictions menu. All users will be able to use the menu. Has a timeout.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(use_emojis="Whether or not responses use emojis for orb names", whitelist_only="Setting to \"Yes\" will only allow users who've been whitelisted to interact with the menu")
@app_commands.choices(
    use_emojis=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ],
    whitelist_only=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ]
)
async def userInstallScrollMenu(
    interaction: discord.Interaction, use_emojis: discord.app_commands.Choice[int], 
    whitelist_only: Optional[discord.app_commands.Choice[int]]):
    
    ephRes = False
    whiteListed = False
    if str(interaction.user.id) in userWhiteList:
        whiteListed = False
        exp = userWhiteList[str(interaction.user.id)].get('expiration')
        whiteListed = True if exp == -1 else exp > time.time()


    if not whiteListed and not disableWhitelisting:
        await interaction.response.send_message(
            content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
            ephemeral=True,
        )
        return
    
    if use_emojis.value == 1 and (
        str(interaction.user.id) not in userSettings
        or "emojis" not in userSettings[str(interaction.user.id)]
    ):
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
            emojis=None
            if use_emojis.value == 0
            else userSettings[str(interaction.user.id)]["emojis"],
        ),
        ephemeral=False,
    )
