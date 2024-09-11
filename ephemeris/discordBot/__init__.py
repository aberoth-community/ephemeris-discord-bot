import time
from typing import Optional
import discord.types
from regex import match
import discord
from discord import app_commands
from discord.ext import commands
from ..Ephemeris import Ephemeris
from .variables import *

ephemeris = Ephemeris.Ephemeris(
    start=(time.time() * 1000) + cacheStartDay * oneDay, end=(time.time() * 1000) + cacheEndDay * oneDay,
    numMoonCycles=numMoonCycles
)
    
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

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == ownerID

async def not_owner_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.CheckFailure):
        await interaction.response.send_message(
                    content=f"Only the bot owner (<@{ownerID}>) may use this command",
                    ephemeral=True,
                )

####################
#    COMMANDS
####################
@bot.tree.command(name="hello")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}!", ephemeral=True
    )

@bot.tree.command(name="update_whitelist", description="Only the bot owner may use this command")
@commands.is_owner()
@app_commands.check(is_owner)
@app_commands.default_permissions()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(user_or_guild="ID of the user or guild you wish to update the settings for", id_type="Specifies if the ID provided is a user ID or guild ID", 
                       expiration="The epoch time in second for which whitelisted status expires. A value of \"-1\" will never expire")
@app_commands.choices(
    id_type=[
        discord.app_commands.Choice(name="User", value=1),
        discord.app_commands.Choice(name="Guild", value=0),
    ],
)
async def updateWhiteList(interaction: discord.Interaction, user_or_guild: str, id_type: discord.app_commands.Choice[int], expiration: int):
    if id_type.name == "User":
        await interaction.response.defer(ephemeral=True, thinking=True)
        userName = ""
        try:
            user = await bot.fetch_user(user_or_guild)
            userName =  user.name
        except discord.NotFound: 
            await interaction.followup.send(f"Error fetching user name for ID {user_or_guild}:\n\"NotFound\"", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(f"Error fetching user name for ID {user_or_guild}:\n\"HTTPException\"", ephemeral=True)
            return
        userWhiteList[user_or_guild] = { "username": userName, "expiration": expiration}
        try:
            UWLPath.write_text(json.dumps(userWhiteList, indent=4))
        except Exception as e:
            await interaction.followup.send(f"Failed to write to userWhiteList file.", ephemeral=True)
            
        await interaction.followup.send(
            f"Whitelist settings updated for <@{user_or_guild}>:\n**New Expiration:**  " + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"), ephemeral=True
            )
        return
    elif id_type.name == "Guild":
        await interaction.response.defer(ephemeral=True, thinking=True)
        userName = ""
        try:
            guild = await bot.fetch_guild(user_or_guild)
            guildName =  guild.name
        except discord.NotFound: 
            await interaction.followup.send(f"Error fetching guild name for ID {user_or_guild}:\n\"NotFound\"", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(f"Error fetching guild name for ID {user_or_guild}:\n\"HTTPException\"", ephemeral=True)
            return
        guildWhiteList[user_or_guild] = { "guild": guildName, "expiration": expiration}
        try:
            GWLPath.write_text(json.dumps(guildWhiteList, indent=4))
        except Exception as e:
            await interaction.followup.send(f"Failed to write to guildWhiteList file.", ephemeral=True)
            
        await interaction.followup.send(
            f"Whitelist settings updated for {guildName}:\n**New Expiration:**  " + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"), ephemeral=True
            )
        return
    
    await interaction.response.send_message(f"Invalid command parameters, action aborted.", ephemeral=True)

@updateWhiteList.error
async def UpdateWLError(interaction: discord.Interaction, error):
    await not_owner_error(interaction, error)


@bot.tree.command(name="permissions", description='Tells the user when their and/or the server\'s access they used it on expires')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def checkPermissions(interaction: discord.Interaction):
    expMsg = ""
    if 0 in interaction._integration_owners:
            expMsg = "**Guild:** "
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
            else: expMsg += "Not White Listed."
    expMsg += "\n**User:** "
    if str(interaction.user.id) in userWhiteList:
        exp = userWhiteList[str(interaction.user.id)].get('expiration')
        expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
    else: expMsg += "Not White Listed."
    
    await interaction.response.send_message(
        content=expMsg,
        ephemeral=True,
    )

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
            content="**Please configure your personal emoji settings (/set_personal_emojis) to use this command __with emojis.__**",
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
    description="Creates lunar calendar menu with no timeout. Requires admin. Usable by all users",
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
        description="*Night will start 42 minutes after the start of each moon phase*",
        #color=0xA21613,
        color=13546768,
    )
    embed.add_field(
        name="**__Details:__**",
        value=f"​\n**`All Moons:      `**\n```Provides a list with the times at which each phase starts for the next {numDisplayMoonCycles} syndonic aberoth months```"
                "\n**`Next Full Moon:`**\n```Provides the time at which the next full moon will start.```"
                "\n**`Next New Moon: `**\n````Provides the time at which the next new moon will start.```"
                "\n**`Filter:        `**\n```Use the drop down menu to select one or more moon phases."
                f"\nA list with the times at which the selected phases start for the next {numDisplayMoonCycles} syndonic aberoth months will be provided```",
        inline=False,
    )
    embed.set_thumbnail(url=scrollThumbnailURL)
    await interaction.response.send_message(
        embed=embed, view=GuildLunarMenu(), ephemeral=False
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
    white: str = defaultEmojis['White'],
    black: str = defaultEmojis['Black'],
    green: str = defaultEmojis['Green'],
    red: str = defaultEmojis['Red'],
    purple: str = defaultEmojis['Purple'],
    yellow: str = defaultEmojis['Yellow'],
    cyan: str = defaultEmojis['Cyan'],
    blue: str = defaultEmojis['Blue'],
    new: Optional[str] = defaultEmojis['new'],
    waxing_crescent: Optional[str] = defaultEmojis['waxing_crescent'],
    first_quarter: Optional[str] = defaultEmojis['first_quarter'],
    waxing_gibbous: Optional[str] = defaultEmojis['waxing_gibbous'],
    full: Optional[str] = defaultEmojis['full'],
    waning_gibbous: Optional[str] = defaultEmojis['waning_gibbous'],
    third_quarter: Optional[str] = defaultEmojis['third_quarter'],
    waning_crescent: Optional[str] = defaultEmojis['waning_crescent'],
    
):
    invalidEmojis = []
    for emoji in (white, black, green, red, purple, yellow, cyan, blue, new, waxing_crescent,
                first_quarter, waxing_gibbous, full, waning_gibbous, third_quarter, waning_crescent):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        if str(interaction.guild_id) in guildSettings:
            guildSettings[str(interaction.guild_id)]["emojis"] = {
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
                "waning_crescent": waning_crescent
            }
        else:
            guildSettings[str(interaction.guild_id)] = {
                "emojis": {
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
                    "waning_crescent": waning_crescent
                }
            }
        emojis = guildSettings[str(interaction.guild_id)]["emojis"]
        updateSettings(settings=guildSettings)
        await interaction.response.send_message(
            content="**Successfully set server emojis!**"
            f"\n> `White            ` {emojis['White']}"
            f"\n> `Black            ` {emojis['Black']}"
            f"\n> `Green            ` {emojis['Green']}"
            f"\n> `Red              ` {emojis['Red']}"
            f"\n> `Purple           ` {emojis['Purple']}"
            f"\n> `Yellow           ` {emojis['Yellow']}"
            f"\n> `Cyan             ` {emojis['Cyan']}"
            f"\n> `Blue             ` {emojis['Blue']}"
            f"\n> `New Moon         ` {emojis['new']}"
            f"\n> `Waxing Crescent  ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter    ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous   ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon        ` {emojis['full']}"
            f"\n> `Waning Gibbous   ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter    ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent  ` {emojis['waning_crescent']}",
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
    white: str = defaultEmojis['White'],
    black: str = defaultEmojis['Black'],
    green: str = defaultEmojis['Green'],
    red: str = defaultEmojis['Red'],
    purple: str = defaultEmojis['Purple'],
    yellow: str = defaultEmojis['Yellow'],
    cyan: str = defaultEmojis['Cyan'],
    blue: str = defaultEmojis['Blue'],
    new: Optional[str] = defaultEmojis['new'],
    waxing_crescent: Optional[str] = defaultEmojis['waxing_crescent'],
    first_quarter: Optional[str] = defaultEmojis['first_quarter'],
    waxing_gibbous: Optional[str] = defaultEmojis['waxing_gibbous'],
    full: Optional[str] = defaultEmojis['full'],
    waning_gibbous: Optional[str] = defaultEmojis['waning_gibbous'],
    third_quarter: Optional[str] = defaultEmojis['third_quarter'],
    waning_crescent: Optional[str] = defaultEmojis['waning_crescent'],
):
    invalidEmojis = []
    for emoji in (white, black, green, red, purple, yellow, cyan, blue, new, waxing_crescent,
                first_quarter, waxing_gibbous, full, waning_gibbous, third_quarter, waning_crescent):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        if str(interaction.user.id) in userSettings:
            userSettings[str(interaction.user.id)]["emojis"] = {
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
                "waning_crescent": waning_crescent
            }
        else:
            userSettings[str(interaction.user.id)] = {
                "emojis": {
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
                    "waning_crescent": waning_crescent
                }
            }
        emojis = userSettings[str(interaction.user.id)]["emojis"]
        updateSettings(settings=userSettings, settingsFile=USPath)
        await interaction.response.send_message(
            content="**Successfully set personal emojis!**"
            f"\n> `White            ` {emojis['White']}"
            f"\n> `Black            ` {emojis['Black']}"
            f"\n> `Green            ` {emojis['Green']}"
            f"\n> `Red              ` {emojis['Red']}"
            f"\n> `Purple           ` {emojis['Purple']}"
            f"\n> `Yellow           ` {emojis['Yellow']}"
            f"\n> `Cyan             ` {emojis['Cyan']}"
            f"\n> `Blue             ` {emojis['Blue']}"
            f"\n> `New Moon         ` {emojis['new']}"
            f"\n> `Waxing Crescent  ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter    ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous   ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon        ` {emojis['full']}"
            f"\n> `Waning Gibbous   ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter    ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent  ` {emojis['waning_crescent']}",
            ephemeral=True,
        )


####################
#      Menus
####################
class GuildDaySelMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True, filterList=None, setUp=False, whiteListUsersOnly=False):
        self.setUp = setUp
        self.whiteListUsersOnly = False
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        options = [discord.SelectOption(label=x) for x in range(selectStartDay, selectEndDay+1)]
        super().__init__(
            placeholder="Select how many days from today",
            options=options,
            custom_id="selectDay",
            min_values=1,
            max_values=2,
        )

    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        messageDefered = False
        
        useEmojis = False
        emojis = None
        if str(interaction.channel_id) in guildSettings[str(interaction.guild_id)]:
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "useEmojis"
                ]
                == 1
            ):
                useEmojis = True
                emojis = guildSettings[str(interaction.guild_id)]["emojis"]
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "whitelisted_users_only"
                ]
                == 1
            ):
                self.whiteListUsersOnly = True
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                if "filters" not in guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)]:
                    guildSettings[str(interaction.guild_id)][
                        str(interaction.channel_id)
                    ]["filters"] = {}

                self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ].get("filters")
        
        if 0 in interaction._integration_owners:
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                whiteListed = True if exp == None or exp == -1 else exp > time.time()
            if self.whiteListUsersOnly:
                if str(interaction.user.id) in userWhiteList:
                    exp = userWhiteList[str(interaction.user.id)].get('expiration')
                    temp = True if exp == -1 else exp > time.time()
                else: temp = False
                whiteListed = whiteListed and temp
        elif 1 in interaction._integration_owners:
            if str(interaction.user.id) in userWhiteList:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        start = min(self.values)
        end = max(self.values)
        dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        if dayList[0] == "Out of Range":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateScrollCache(start=(time.time() * 1000) + cacheStartDay * oneDay, stop=(time.time() * 1000) + cacheEndDay * oneDay)
            dayList = dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        msgArr = splitMsg(dayList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


class UserInstallSelDayMenu(discord.ui.Select):
    def __init__(
        self, ephemeralRes=True, filterList=None, useEmojis=False, emojis=None, whiteListOnly=False
    ):
        self.ephemeralRes = ephemeralRes
        self.useEmojis = useEmojis
        self.emojis = emojis
        self.whiteListOnly = whiteListOnly
        self.filterList = filterList
        options = [discord.SelectOption(label=x) for x in range(selectStartDay, selectEndDay+1)]
        super().__init__(
            placeholder="Select how many days from today",
            options=options,
            min_values=1,
            max_values=2,
        )

    async def callback(self, interaction: discord.Interaction):
        whiteListed = True
        messageDefered = False
        if self.whiteListOnly:
            if not str(interaction.user.id) in userWhiteList:
                whiteListed = False
            else:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
                ephemeral=True,
            )
            return
        start = min(self.values)
        end = max(self.values)
        dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        if dayList[0] == "Out of Range":
            await interaction.response.defer(ephemeral=False, thinking=True)
            messageDefered = True
            ephemeris.updateScrollCache(start=(time.time() * 1000) + cacheStartDay * oneDay, stop=(time.time() * 1000) + cacheEndDay * oneDay)
            dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        msgArr = splitMsg(dayList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


class GuildPhaseSelMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True, filterList=None, setUp=False, whiteListUsersOnly=False):
        self.setUp = setUp
        self.whiteListUsersOnly = False
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        options = [discord.SelectOption(label=x) for x in range(selectStartDay, selectEndDay+1)]
        super().__init__(
            placeholder="Select which phases",
            options=options,
            custom_id="phaseFilter",
            min_values=1,
            max_values=8,
        )

    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        messageDefered = False
        
        useEmojis = False
        emojis = None
        if str(interaction.channel_id) in guildSettings[str(interaction.guild_id)]:
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "useEmojis"
                ]
                == 1
            ):
                useEmojis = True
                emojis = guildSettings[str(interaction.guild_id)]["emojis"]
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "whitelisted_users_only"
                ]
                == 1
            ):
                self.whiteListUsersOnly = True
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                if "filters" not in guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)]:
                    guildSettings[str(interaction.guild_id)][
                        str(interaction.channel_id)
                    ]["filters"] = {}

                self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ].get("filters")
        
        if 0 in interaction._integration_owners:
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                whiteListed = True if exp == None or exp == -1 else exp > time.time()
            if self.whiteListUsersOnly:
                if str(interaction.user.id) in userWhiteList:
                    exp = userWhiteList[str(interaction.user.id)].get('expiration')
                    temp = True if exp == -1 else exp > time.time()
                else: temp = False
                whiteListed = whiteListed and temp
        elif 1 in interaction._integration_owners:
            if str(interaction.user.id) in userWhiteList:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        start = min(self.values)
        end = max(self.values)
        dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        if dayList[0] == "Out of Range":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateScrollCache(start=(time.time() * 1000) + cacheStartDay * oneDay, stop=(time.time() * 1000) + cacheEndDay * oneDay)
            dayList = dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        msgArr = splitMsg(dayList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


class UserInstallFilterMenu(discord.ui.Select):
    def __init__(
        self, filterOptions, initiationTime, timeout=300, useEmojis=False, emojis=None, whiteListOnly=False
    ):
        self.timeout = timeout
        self.filterOptions = filterOptions
        self.initiationTime = initiationTime
        self.useEmojis = useEmojis
        self.emojis = emojis
        self.whiteListOnly = whiteListOnly
        options = [
            discord.SelectOption(
                label="White",
                value="White",
                emoji=defaultEmojis["White"],
                default=filterOptions["White"],
            ),
            discord.SelectOption(
                label="Black",
                value="Black",
                emoji=defaultEmojis["Black"],
                default=filterOptions["Black"],
            ),
            discord.SelectOption(
                label="Green",
                value="Green",
                emoji=defaultEmojis["Green"],
                default=filterOptions["Green"],
            ),
            discord.SelectOption(
                label="Red",
                value="Red",
                emoji=defaultEmojis["Red"],
                default=filterOptions["Red"],
            ),
            discord.SelectOption(
                label="Purple",
                value="Purple",
                emoji=defaultEmojis["Purple"],
                default=filterOptions["Purple"],
            ),
            discord.SelectOption(
                label="Yellow",
                value="Yellow",
                emoji=defaultEmojis["Yellow"],
                default=filterOptions["Yellow"],
            ),
            discord.SelectOption(
                label="Cyan",
                value="Cyan",
                emoji=defaultEmojis["Cyan"],
                default=filterOptions["Cyan"],
            ),
            discord.SelectOption(
                label="Blue",
                value="Blue",
                emoji=defaultEmojis["Blue"],
                default=filterOptions["Blue"],
            ),
        ]
        super().__init__(
            placeholder="Scroll events to display (Default All)",
            options=options,
            min_values=0,
            max_values=8,
        )

    async def callback(self, interaction: discord.Interaction):
        # This is done so all users will see the same selected options
        filterOptions = {
            "White": False,
            "Black": False,
            "Green": False,
            "Red": False,
            "Purple": False,
            "Yellow": False,
            "Cyan": False,
            "Blue": False,
        }
        filterList = []
        for orb in self.values:
            filterOptions[orb] = True
            filterList.append(orb)
        # change select menu options
        newTimeoutTime = self.timeout - (time.time() - self.initiationTime)
        if newTimeoutTime < 1:
            newTimeoutTime = 0
        await interaction.response.edit_message(
            view=UserInstallScrollMenu(
                timeout=newTimeoutTime,
                filterOptions=filterOptions,
                filterList=filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
                whiteListOnly=self.whiteListOnly
            )
        )


class GuildFilterMenu(discord.ui.Select):
    def __init__(self, filterOptions=None, timeout=None):
        self.timeout = timeout
        if filterOptions == None:
            filterOptions = {
                "White": False,
                "Black": False,
                "Green": False,
                "Red": False,
                "Purple": False,
                "Yellow": False,
                "Cyan": False,
                "Blue": False,
            }
        options = [
            discord.SelectOption(
                label="White",
                value="White",
                emoji=defaultEmojis["White"],
                default=filterOptions["White"],
            ),
            discord.SelectOption(
                label="Black",
                value="Black",
                emoji=defaultEmojis["Black"],
                default=filterOptions["Black"],
            ),
            discord.SelectOption(
                label="Green",
                value="Green",
                emoji=defaultEmojis["Green"],
                default=filterOptions["Green"],
            ),
            discord.SelectOption(
                label="Red",
                value="Red",
                emoji=defaultEmojis["Red"],
                default=filterOptions["Red"],
            ),
            discord.SelectOption(
                label="Purple",
                value="Purple",
                emoji=defaultEmojis["Purple"],
                default=filterOptions["Purple"],
            ),
            discord.SelectOption(
                label="Yellow",
                value="Yellow",
                emoji=defaultEmojis["Yellow"],
                default=filterOptions["Yellow"],
            ),
            discord.SelectOption(
                label="Cyan",
                value="Cyan",
                emoji=defaultEmojis["Cyan"],
                default=filterOptions["Cyan"],
            ),
            discord.SelectOption(
                label="Blue",
                value="Blue",
                emoji=defaultEmojis["Blue"],
                default=filterOptions["Blue"],
            ),
        ]
        super().__init__(
            placeholder="Scroll events to display (Default All)",
            options=options,
            min_values=0,
            max_values=8,
            custom_id="filterOptions",
        )

    async def callback(self, interaction: discord.Interaction):
        # This is done so all users will see the same selected options
        filterOptions = {
            "White": False,
            "Black": False,
            "Green": False,
            "Red": False,
            "Purple": False,
            "Yellow": False,
            "Cyan": False,
            "Blue": False,
        }
        filterList = []
        for orb in self.values:
            filterOptions[orb] = True
            filterList.append(orb)
        guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
            "filters"
        ] = filterList
        updateSettings(settings=guildSettings)
        # change select menu options
        await interaction.response.edit_message(
            view=GuildScrollMenu(
                timeout=None,
                filterOptions=filterOptions,
                filterList=filterList,
                allow_filters=1,
            )
        )


class UserInstallScrollMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=False,
        timeout=300,
        useEmojis=False,
        emojis=None,
        whiteListOnly=False,
        filterList=None,
        filterOptions={
            "White": False,
            "Black": False,
            "Green": False,
            "Red": False,
            "Purple": False,
            "Yellow": False,
            "Cyan": False,
            "Blue": False,
        },
    ):
        super().__init__(timeout=timeout)
        self.initiationTime = time.time()
        self.filterOptions = filterOptions
        self.ephemeralRes = ephemeralRes
        self.useEmojis = useEmojis,
        self.whiteListOnly = whiteListOnly
        self.emojis = emojis
        self.filterList = filterList
        self.add_item(
            UserInstallSelDayMenu(
                ephemeralRes, filterList, useEmojis=useEmojis, emojis=emojis, whiteListOnly=whiteListOnly
            )
        )
        self.add_item(
            UserInstallFilterMenu(
                self.filterOptions,
                initiationTime=self.initiationTime,
                timeout=timeout,
                useEmojis=useEmojis,
                emojis=emojis,
                whiteListOnly=self.whiteListOnly
            )
        )

    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red)
    async def yesterday(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.userMenuBtnPress(interaction=interaction, button=button)
        
    @discord.ui.button(label="Today", style=discord.ButtonStyle.green)
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.userMenuBtnPress(interaction=interaction, button=button)
        
    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple)
    async def tomorrow(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.userMenuBtnPress(interaction=interaction, button=button)
    
    
    async def userMenuBtnPress(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = True
        messageDefered = False
        if self.whiteListOnly:
            if not str(interaction.user.id) in userWhiteList:
                whiteListed = False
            else:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()
        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        startDays = {"Yesterday": -1, "Today": 0, "Tomorrow": 1}
        dayList = getDayList(
                ephemeris,
                startDay=startDays[button.label],
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        if dayList[0] == "Out of Range":
            await interaction.response.defer(ephemeral=False, thinking=True)
            messageDefered = True
            ephemeris.updateScrollCache(start=(time.time() * 1000) + cacheStartDay * oneDay, stop=(time.time() * 1000) + cacheEndDay * oneDay)
            dayList = getDayList(
                ephemeris,
                startDay=startDays[button.label],
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        
        msgArr = splitMsg(dayList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


# Create seperate menu that will persist
class GuildScrollMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=True,
        timeout=None,
        allow_filters=None,
        filterOptions=None,
        filterList=None,
        setUp=True,
    ):
        super().__init__(timeout=timeout)
        self.setUp = setUp
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        self.allow_filters = allow_filters
        self.whiteListUsersOnly = False
        self.add_item(GuildDaySelMenu(ephemeralRes, self.setUp))
        if self.allow_filters == 1:
            self.add_item(GuildFilterMenu(filterOptions))

    @discord.ui.button(
        label="Yesterday", style=discord.ButtonStyle.red, custom_id="yesterday"
    )
    async def yesterday(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.guildScrollMenuBtnPress(interaction=interaction, button=button)

    @discord.ui.button(
        label="Today", style=discord.ButtonStyle.green, custom_id="today"
    )
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildScrollMenuBtnPress(interaction=interaction, button=button)
        
    @discord.ui.button(
        label="Tomorrow", style=discord.ButtonStyle.blurple, custom_id="tomorrow"
    )
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildScrollMenuBtnPress(interaction=interaction, button=button)
    
    async def guildScrollMenuBtnPress(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        messageDefered = False
        
        useEmojis = False
        emojis = None
        if str(interaction.channel_id) in guildSettings[str(interaction.guild_id)]:
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "useEmojis"
                ]
                == 1
            ):
                useEmojis = True
                emojis = guildSettings[str(interaction.guild_id)]["emojis"]
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "whitelisted_users_only"
                ]
                == 1
            ):
                self.whiteListUsersOnly = True
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                if "filters" not in guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)]:
                    guildSettings[str(interaction.guild_id)][
                        str(interaction.channel_id)
                    ]["filters"] = {}

                self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ].get("filters")
                
        if 0 in interaction._integration_owners:
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()
            if self.whiteListUsersOnly:
                if str(interaction.user.id) in userWhiteList:
                    exp = userWhiteList[str(interaction.user.id)].get('expiration')
                    temp = True if exp == -1 else exp > time.time()
                else: temp = False
                whiteListed = whiteListed and temp
        elif 1 in interaction._integration_owners:
            if str(interaction.user.id) in userWhiteList:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        startDays = {"Yesterday": -1, "Today": 0, "Tomorrow": 1}
        dayList = getDayList(
                ephemeris,
                startDay=startDays[button.label],
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        if dayList[0] == "Out of Range":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateScrollCache(start=(time.time() * 1000) + cacheStartDay * oneDay, stop=(time.time() * 1000) + cacheEndDay * oneDay)
            dayList = getDayList(
                ephemeris,
                startDay=startDays[button.label],
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        
        msgArr = splitMsg(dayList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


# Create seperate menu that will persist
class GuildLunarMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=True,
        timeout=None
    ):
        super().__init__(timeout=timeout)
        self.ephemeralRes = ephemeralRes
        self.whiteListUsersOnly = False
        self.add_item(GuildPhaseSelMenu(ephemeralRes))

    @discord.ui.button(
        label="All Moon Phases", style=discord.ButtonStyle.red, custom_id="all"
    )
    async def allPhases(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button)

    @discord.ui.button(
        label="Next Full Moon", style=discord.ButtonStyle.green, custom_id="full"
    )
    async def fullMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button)
        
    @discord.ui.button(
        label="Next New Moon", style=discord.ButtonStyle.blurple, custom_id="new"
    )
    async def newMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button)
        
    @discord.ui.button(
        label="Current Phase", style=discord.ButtonStyle.blurple, custom_id="current"
    )
    async def newMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button)
    
    async def guildLunarMenuBtnPress(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        messageDefered = False
        
        useEmojis = False
        emojis = None
        if str(interaction.channel_id) in guildSettings[str(interaction.guild_id)]:
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "useEmojis"
                ]
                == 1
            ):
                useEmojis = True
                emojis = guildSettings[str(interaction.guild_id)]["emojis"]
            if (
                guildSettings[str(interaction.guild_id)][str(interaction.channel_id)][
                    "whitelisted_users_only"
                ]
                == 1
            ):
                self.whiteListUsersOnly = True
                
        if 0 in interaction._integration_owners:
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()
            if self.whiteListUsersOnly:
                if str(interaction.user.id) in userWhiteList:
                    exp = userWhiteList[str(interaction.user.id)].get('expiration')
                    temp = True if exp == -1 else exp > time.time()
                else: temp = False
                whiteListed = whiteListed and temp
        elif 1 in interaction._integration_owners:
            if str(interaction.user.id) in userWhiteList:
                exp = userWhiteList[str(interaction.user.id)].get('expiration')
                whiteListed = True if exp == -1 else exp > time.time()

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        phaseList = getPhaseList(
                        ephemeris,
                        filters = None,
                        useEmojis=useEmojis,
                        emojis=emojis)
        
        if phaseList[0] == "Range too Small":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateMoonCache((time.time() * 1000), numDisplayMoonCycles)
            phaseList = getPhaseList(
                ephemeris,
                filters=None,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        
        msgArr = splitMsg(phaseList)
        if messageDefered:
            await interaction.followup.send(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        else:
            await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )

#######################
#  Helper Functions
#######################
def getDayList(
    ephemeris:Ephemeris,
    startDay: int,
    useEmojis:bool=False,
    filters:dict=None,
    emojis:dict=None,
    endDay: int = None,
):
    currentTime = round((time.time() * 1000))
    start = (
        currentTime - round(0.25 * oneDay)
        if startDay == 0
        else currentTime + int(startDay) * int(oneDay)
    )
    if endDay == None:
        end = currentTime + oneDay if startDay == 0 else start + oneDay
    else:
        end = currentTime + int(oneDay) * int(endDay) + oneDay
    # print(f"End: {end}\nEnd: {ephemeris.scrollEventsCache[-1][0]}")
    if end >= ephemeris.scrollEventsCache[-1][0]:
        # print("end out of range")
        return ['Out of Range']
    cacheSubSet = ephemeris.getScrollEventsInRange(start, end)

    # filter out specific orb events
    if filters != None and len(filters) != 0:
        tempCache = []
        for e in cacheSubSet:
            for orb in filters:
                if (
                    orb in e["newGlows"]
                    or orb in e["newDarks"]
                    or orb in e["returnedToNormal"]
                ):
                    tempCache.append(e)
                    break
        cacheSubSet = tempCache

    if len(cacheSubSet) == 0:
        if filters != None and len(filters) != 0:
            return "> **There are no events within the selected range that match the applied filters.**"
        else:
            return "> **There are no events within the selected range.**"
    startState = cacheSubSet[0]
    eventMsg = createScrollEventMsgLine(startState, useEmojis, True, emojis=emojis)
    if len(cacheSubSet) > 1:
        for event in cacheSubSet[1:]:
            eventMsg += "\n" + createScrollEventMsgLine(event, useEmojis, emojis=emojis)
    return eventMsg

def getPhaseList(ephemeris:Ephemeris, startTime:int = None, filters:dict = None, useEmojis:bool=False, emojis:dict=None):
    start = startTime
    if start == None:
        currentTime = round((time.time() * 1000))
        start = currentTime - ephemeris.oneAberothDay
    
    startIndex = next((i for i, (timestamp, _) in enumerate(ephemeris.moonCyclesCache) if timestamp > start), None)
    
    subCache = []
    if startIndex:
        subCache = ephemeris.moonCyclesCache[startIndex:]
    if len(subCache) < numDisplayMoonCycles * 10:
        print(subCache, '\n', numDisplayMoonCycles*10, len(subCache))
        return ['Range too Small']
    
    if filters != None and len(filters) != 0:
        subCache = [event for event in subCache if event[1].phase in filters]
    
    startPhase = subCache[0]
    eventMsg = createLunarEventMsgLine(startPhase, useEmojis, emojis=emojis)
    if len(subCache) > 1:
        for event in subCache[1:]:
            eventMsg += "\n" + createLunarEventMsgLine(event, useEmojis, emojis=emojis)
    return eventMsg

def createLunarEventMsgLine(event:tuple[int, dict[str, str]], useEmojis:bool=True, emojis:dict=None) -> str:
    if useEmojis and emojis != None:
        return f"> {emojis[event[1]['phase']]} {event[1]['discordTS']} the moon is {moonDisplayNames[event[1]['phase']]}."
    else: return f"> {defaultEmojis[event[1]['phase']]} {event[1]['discordTS']} {moonDisplayNames[event[1]['phase']]}."
    

def createScrollEventMsgLine(event, useEmojis=True, firstEvent=False, emojis=None) -> str:
    glows = event["newGlows"]
    darks = [i for i in event["newDarks"] if i != "Shadow"]
    normals = [i for i in event["returnedToNormal"] if i != "Shadow"]
    msg = f"> {event['discordTS']}"
    for index, cat in enumerate([glows, darks, normals]):
        tempMsg = ""
        if len(cat) < 1:
            continue
        elif len(cat) >= 3:
            if useEmojis and emojis != None:
                tempMsg += " " + "".join([emojis[orb] for orb in cat]) + " have "
            else:
                tempMsg += (
                    " __"
                    + "__, __".join(cat[:-1])
                    + "__, and __"
                    + cat[-1]
                    + "__ have "
                )
        elif len(cat) == 2:
            if useEmojis and emojis != None:
                tempMsg += " " + "".join([emojis[orb] for orb in cat]) + " have "
            else:
                tempMsg += " __" + cat[0] + "__ and __" + cat[1] + "__ have "
        elif len(cat) == 1:
            if useEmojis and emojis != None:
                tempMsg += " " + emojis[cat[0]] + " has "
            else:
                tempMsg += " __" + cat[0] + "__ has "

        if index == 0:
            tempMsg += "begun to **glow.**"
        elif index == 1:
            tempMsg += "gone **dark.**"
        elif index == 2:
            tempMsg += "returned to **normal.**"

        msg += tempMsg
    return msg

def splitMsg(msg):
    msgArr = []
    while len(msg) > 2000:
        # find last index in range
        i = msg[:2000].rfind("\n")
        msgArr.append(msg[:i])
        msg = msg[i:]
    msgArr.append(msg)
    return msgArr

def updateSettings(settings, settingsFile:Path=GSPath):
    json_object = json.dumps(settings, indent=4)
    with open(settingsFile, "w") as outfile:
        outfile.write(json_object)

def getSettings(settingsFile:Path=GSPath):
    settings = {}
    with open(settingsFile, "r") as json_file:
        settings = json.load(json_file)
    return settings

def isEmoji(emojiStr:str) -> bool:
    """Checks if the argument is an emoji

    Args:
        str (_type_): the string to check if it's an emoji

    Returns:
        Boolean: True if string is an emoji, False if string is not an emoji
    """
    if bool(match(r"\p{Emoji}", emojiStr)):
        return True
    if len(emojiStr) < 5:
        return False
    if emojiStr[:2] + emojiStr[-1] == "<:>" or emojiStr[0] + emojiStr[-1] == "::":
        return True
    else:
        return False
