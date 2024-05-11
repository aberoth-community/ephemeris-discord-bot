import time
import json
from regex import match
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
from ..Ephemeris import Ephemeris

guildSettings = {}
userSettings = {}
guildWhiteList = {}
userWhiteList = {}

GSPath = Path("ephemeris/discordBot/guildSettings.json").absolute()
USPath = Path("ephemeris/discordBot/userSettings.json").absolute()
GWLPath = Path("ephemeris/discordBot/guildWhiteList.json").absolute()
UWLPath = Path("ephemeris/discordBot/userWhiteList.json").absolute()

if not GSPath.exists():
    GSPath.write_text(json.dumps({}))
    print(f"File created: {GSPath}")

if not USPath.exists():
    USPath.write_text(json.dumps({}))
    print(f"File created: {USPath}")

with GSPath.open("r") as f:
    guildSettings = json.load(f)
with USPath.open("r") as f:
    userSettings = json.load(f)
with GWLPath.open("r") as f:
    guildWhiteList = json.load(f)
with UWLPath.open("r") as f:
    userWhiteList = json.load(f)

filterMenuEmojis = {
    "White": "<:WhiteOrb:998472151965376602>",
    "Black": "<:BlackOrb:998472215295164418>",
    "Green": "<:GreenOrb:998472231640379452>",
    "Red": "<:RedOrb:998472356303478874>",
    "Purple": "<:PurpleOrb:998472375400149112>",
    "Yellow": "<:YellowOrb:998472388406689812>",
    "Cyan": "<:CyanOrb:998472398707888229>",
    "Blue": "<:BlueOrb:998472411861233694>",
}

thumbnailURL = "https://i.imgur.com/Lpa96Ry.png"
oneDay = 86400000
ephemeris = Ephemeris.Ephemeris(
    start=(time.time() * 1000) - 2 * 86400000, end=(time.time() * 1000) + 16 * 86400000
)


class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix="", intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(GuildMenu(allow_filters=1, setUp=False))


bot = PersistentViewBot()


@bot.event
async def on_ready():
    print("Bot is up and ready!")
    try:
        synched = await bot.tree.sync()
        print(f"synched {len(synched)} command(s)")
    except Exception as e:
        print(e)


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


@bot.tree.command(
    name="prediction_menu",
    description="Creates predictions menu. All users will be able to use the menu. Has a timeout.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(use_emojis="Whether or not responses use emojis for orb names")
@app_commands.choices(
    use_emojis=[
        discord.app_commands.Choice(name="Yes", value=1),
        discord.app_commands.Choice(name="No", value=0),
    ]
)
async def userInstallMenu(
    interaction: discord.Interaction, use_emojis: discord.app_commands.Choice[int]
):
    ephRes = False
    if str(interaction.user.id) not in userWhiteList:
        await interaction.response.send_message(
            content="You do not have permission to use this command", ephemeral=True
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
    embed.set_thumbnail(url=thumbnailURL)
    embed.set_footer(text="⏱️ Menu expires in five minutes")
    await interaction.response.send_message(
        embed=embed,
        view=UserInstallMenu(
            useEmojis=True if use_emojis.value == 1 else False,
            emojis=None
            if use_emojis.value == 0
            else userSettings[str(interaction.user.id)]["emojis"],
        ),
        ephemeral=False,
    )


@bot.tree.command(
    name="create_persistent_menu",
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
)
async def guildMenu(
    interaction: discord.Interaction,
    use_emojis: discord.app_commands.Choice[int],
    allow_filters: discord.app_commands.Choice[int],
):
    ephRes = True
    if str(interaction.guild_id) not in guildWhiteList:
        await interaction.response.send_message(
            content="Server does not have permission to use this command",
            ephemeral=True,
        )
        return
    if str(interaction.guild_id) in guildSettings:
        guildSettings[str(interaction.guild_id)][str(interaction.channel_id)] = {
            "useEmojis": use_emojis.value,
            "allow_filters": allow_filters.value,
        }
    else:
        guildSettings[str(interaction.guild_id)] = {
            str(interaction.channel_id): {
                "useEmojis": use_emojis.value,
                "allow_filters": allow_filters.value,
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
    embed.set_thumbnail(url=thumbnailURL)
    await interaction.response.send_message(
        embed=embed, view=GuildMenu(allow_filters=allow_filters.value), ephemeral=False
    )


@bot.tree.command(
    name="set_server_emojis",
    description="Configures the emojis used for ephemerides requested from prediction menus used within the server.",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def setServerEmojis(
    interaction: discord.Interaction,
    white: str,
    black: str,
    green: str,
    red: str,
    purple: str,
    yellow: str,
    cyan: str,
    blue: str,
):
    invalidEmojis = []
    for emoji in white, black, green, red, purple, yellow, cyan, blue:
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
                }
            }
        emojis = guildSettings[str(interaction.guild_id)]["emojis"]
        updateSettings(settings=guildSettings)
        await interaction.response.send_message(
            content="**Successfully set server emojis!**"
            f"\n> `White ` {emojis['White']}"
            f"\n> `Black ` {emojis['Black']}"
            f"\n> `Green ` {emojis['Green']}"
            f"\n> `Red   ` {emojis['Red']}"
            f"\n> `Purple` {emojis['Purple']}"
            f"\n> `Yellow` {emojis['Yellow']}"
            f"\n> `Cyan  ` {emojis['Cyan']}"
            f"\n> `Blue  ` {emojis['Blue']}",
            ephemeral=True,
        )


@bot.tree.command(
    name="set_personal_emojis",
    description="Configures the emojis used for ephemerides requested from user installable prediction menus",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe()
async def setPersonalEmojis(
    interaction: discord.Interaction,
    white: str,
    black: str,
    green: str,
    red: str,
    purple: str,
    yellow: str,
    cyan: str,
    blue: str,
):
    invalidEmojis = []
    for emoji in white, black, green, red, purple, yellow, cyan, blue:
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
                }
            }
        emojis = userSettings[str(interaction.user.id)]["emojis"]
        updateSettings(settings=userSettings, settingsFile=USPath)
        await interaction.response.send_message(
            content="**Successfully set personal emojis!**"
            f"\n> `White ` {emojis['White']}"
            f"\n> `Black ` {emojis['Black']}"
            f"\n> `Green ` {emojis['Green']}"
            f"\n> `Red   ` {emojis['Red']}"
            f"\n> `Purple` {emojis['Purple']}"
            f"\n> `Yellow` {emojis['Yellow']}"
            f"\n> `Cyan  ` {emojis['Cyan']}"
            f"\n> `Blue  ` {emojis['Blue']}",
            ephemeral=True,
        )


####################
#      Menus
####################
class GuildDaySelMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True, filterList=None, setUp=False):
        self.setUp = setUp
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        options = [discord.SelectOption(label=x) for x in range(-1, 15)]
        super().__init__(
            placeholder="Select how many days from today",
            options=options,
            custom_id="selectDay",
            min_values=1,
            max_values=2,
        )

    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return
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
                ]["filters"]

        start = min(self.values)
        end = max(self.values)
        msgArr = splitMsg(
            getDayList(
                ephemeris,
                startDay=start,
                useEmojis=useEmojis,
                filters=self.filterList,
                emojis=emojis,
                endDay=end,
            )
        )
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
        self, ephemeralRes=True, filterList=None, useEmojis=False, emojis=None
    ):
        self.ephemeralRes = ephemeralRes
        self.useEmojis = useEmojis
        self.emojis = emojis
        self.filterList = filterList
        options = [discord.SelectOption(label=x) for x in range(-1, 15)]
        super().__init__(
            placeholder="Select how many days from today",
            options=options,
            min_values=1,
            max_values=2,
        )

    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return
        start = min(self.values)
        end = max(self.values)
        msgArr = splitMsg(
            getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        )
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
        self, filterOptions, initiationTime, timeout=300, useEmojis=False, emojis=None
    ):
        self.timeout = timeout
        self.filterOptions = filterOptions
        self.initiationTime = initiationTime
        self.useEmojis = useEmojis
        self.emojis = emojis
        options = [
            discord.SelectOption(
                label="White",
                value="White",
                emoji=filterMenuEmojis["White"],
                default=filterOptions["White"],
            ),
            discord.SelectOption(
                label="Black",
                value="Black",
                emoji=filterMenuEmojis["Black"],
                default=filterOptions["Black"],
            ),
            discord.SelectOption(
                label="Green",
                value="Green",
                emoji=filterMenuEmojis["Green"],
                default=filterOptions["Green"],
            ),
            discord.SelectOption(
                label="Red",
                value="Red",
                emoji=filterMenuEmojis["Red"],
                default=filterOptions["Red"],
            ),
            discord.SelectOption(
                label="Purple",
                value="Purple",
                emoji=filterMenuEmojis["Purple"],
                default=filterOptions["Purple"],
            ),
            discord.SelectOption(
                label="Yellow",
                value="Yellow",
                emoji=filterMenuEmojis["Yellow"],
                default=filterOptions["Yellow"],
            ),
            discord.SelectOption(
                label="Cyan",
                value="Cyan",
                emoji=filterMenuEmojis["Cyan"],
                default=filterOptions["Cyan"],
            ),
            discord.SelectOption(
                label="Blue",
                value="Blue",
                emoji=filterMenuEmojis["Blue"],
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
            view=UserInstallMenu(
                timeout=newTimeoutTime,
                filterOptions=filterOptions,
                filterList=filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
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
                emoji=filterMenuEmojis["White"],
                default=filterOptions["White"],
            ),
            discord.SelectOption(
                label="Black",
                value="Black",
                emoji=filterMenuEmojis["Black"],
                default=filterOptions["Black"],
            ),
            discord.SelectOption(
                label="Green",
                value="Green",
                emoji=filterMenuEmojis["Green"],
                default=filterOptions["Green"],
            ),
            discord.SelectOption(
                label="Red",
                value="Red",
                emoji=filterMenuEmojis["Red"],
                default=filterOptions["Red"],
            ),
            discord.SelectOption(
                label="Purple",
                value="Purple",
                emoji=filterMenuEmojis["Purple"],
                default=filterOptions["Purple"],
            ),
            discord.SelectOption(
                label="Yellow",
                value="Yellow",
                emoji=filterMenuEmojis["Yellow"],
                default=filterOptions["Yellow"],
            ),
            discord.SelectOption(
                label="Cyan",
                value="Cyan",
                emoji=filterMenuEmojis["Cyan"],
                default=filterOptions["Cyan"],
            ),
            discord.SelectOption(
                label="Blue",
                value="Blue",
                emoji=filterMenuEmojis["Blue"],
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
            view=GuildMenu(
                timeout=None,
                filterOptions=filterOptions,
                filterList=filterList,
                allow_filters=1,
            )
        )


class UserInstallMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=False,
        timeout=300,
        useEmojis=False,
        emojis=None,
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
        self.useEmojis = useEmojis
        self.emojis = emojis
        self.filterList = filterList
        self.add_item(
            UserInstallSelDayMenu(
                ephemeralRes, filterList, useEmojis=useEmojis, emojis=emojis
            )
        )
        self.add_item(
            UserInstallFilterMenu(
                self.filterOptions,
                initiationTime=self.initiationTime,
                timeout=timeout,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        )

    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red)
    async def yesterday(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                -1,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        )
        await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )

    @discord.ui.button(label="Today", style=discord.ButtonStyle.green)
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                0,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        )
        await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )

    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple)
    async def tomorrow(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                1,
                filters=self.filterList,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
            )
        )
        await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )


# Create seperate menu that will persist
class GuildMenu(discord.ui.View):
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
        self.add_item(GuildDaySelMenu(ephemeralRes, self.setUp))
        if self.allow_filters == 1:
            self.add_item(GuildFilterMenu(filterOptions))

    @discord.ui.button(
        label="Yesterday", style=discord.ButtonStyle.red, custom_id="yesterday"
    )
    async def yesterday(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return
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
                "emojis"
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ]["filters"]

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                startDay=-1,
                useEmojis=useEmojis,
                filters=self.filterList,
                emojis=emojis,
            )
        )
        await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )

    @discord.ui.button(
        label="Today", style=discord.ButtonStyle.green, custom_id="today"
    )
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return
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
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                if 'filters' in guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ]:
                    self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ]["filters"]
                else:
                    self.filterList = {}
                    guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                    ]["filters"] = {}

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                startDay=0,
                useEmojis=useEmojis,
                filters=self.filterList,
                emojis=emojis,
            )
        )
        await interaction.response.send_message(
            content=msgArr[0], ephemeral=self.ephemeralRes
        )
        if len(msgArr) > 1:
            for msg in msgArr[1:]:
                await interaction.followup.send(
                    content=msg, ephemeral=self.ephemeralRes
                )

    @discord.ui.button(
        label="Tomorrow", style=discord.ButtonStyle.blurple, custom_id="tomorrow"
    )
    async def tomorrow(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList

        if not whiteListed:
            await interaction.response.send_message(
                content="Server or user does not have permission to use this command",
                ephemeral=True,
            )
            return

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
            if self.setUp == False:
                # Asignmenu state on interaction when bot is restarted
                self.setUp = True
                self.filterList = guildSettings[str(interaction.guild_id)][
                    str(interaction.channel_id)
                ]["filters"]

        msgArr = splitMsg(
            getDayList(
                ephemeris,
                startDay=1,
                useEmojis=useEmojis,
                filters=self.filterList,
                emojis=emojis,
            )
        )
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
    ephemeris,
    startDay: int,
    useEmojis=False,
    filters=None,
    emojis=None,
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
    cacheSubSet = ephemeris.getEventsInRange(start, end)

    # filter out specific orb events
    if filters != None and len(filters) != 0 and bool(filters) != False:
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
        if filters != None:
            return "> **There are no events within the selected range that match the applied filters.**"
        else:
            return "> **There are no events within the selected range.**"
    startState = cacheSubSet[0]
    eventMsg = createEventMsgLine(startState, useEmojis, True, emojis=emojis)
    if len(cacheSubSet) > 1:
        for event in cacheSubSet[1:]:
            eventMsg += "\n" + createEventMsgLine(event, useEmojis, emojis=emojis)
    return eventMsg


def createEventMsgLine(event, useEmojis=True, firstEvent=False, emojis=None):
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


def updateSettings(settings, settingsFile=GSPath):
    json_object = json.dumps(settings, indent=4)
    with open(settingsFile, "w") as outfile:
        outfile.write(json_object)


def getSettings(settingsFile=GSPath):
    settings = {}
    with open(settingsFile, "r") as json_file:
        settings = json.load(json_file)
    return settings


def isEmoji(str):
    """Checks if the argument is an emoji

    Args:
        str (_type_): the string to check if it's an emoji

    Returns:
        Boolean: True if string is an emoji, False if string is not an emoji
    """
    if bool(match(r"\p{Emoji}", str)):
        return True
    if len(str) < 5:
        return False
    if str[:2] + str[-1] == "<:>" or str[0] + str[-1] == "::":
        return True
    else:
        return False
