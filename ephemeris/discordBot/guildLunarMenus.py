from .commonImports import *
from .bot import ephemeris
from .helperFuncs import splitMsg, getPhaseList

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
        label=lunarLabels["all"], style=discord.ButtonStyle.green, custom_id="all", emoji=defaultEmojis['lunation']
    )
    async def allPhases(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button)

    @discord.ui.button(
        label=lunarLabels['next_full'], style=discord.ButtonStyle.primary, custom_id="full", emoji=defaultEmojis['full']
    )
    async def fullMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
        
    @discord.ui.button(
        label=lunarLabels['next_new'], style=discord.ButtonStyle.grey, custom_id="new", emoji=defaultEmojis['new']
    )
    async def newMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
        
    @discord.ui.button(
        label=lunarLabels['current'], style=discord.ButtonStyle.grey, custom_id="current",  emoji='❔'
    )
    async def currentPhase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.guildLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
    
    async def guildLunarMenuBtnPress(self, interaction: discord.Interaction, button: discord.ui.Button, firstEventOnly:bool = False):
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
                        filters = [button.label],
                        useEmojis=useEmojis,
                        emojis=emojis,
                        firstEventOnly=firstEventOnly
                        )
        
        if phaseList[0] == "Range too Small":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateMoonCache((time.time() * 1000), numDisplayMoonCycles)
            phaseList = getPhaseList(
                ephemeris,
                filters=[button.label],
                useEmojis=useEmojis,
                emojis=emojis,
                firstEventOnly=firstEventOnly
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

class GuildPhaseSelMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True, whiteListUsersOnly=False):
        self.whiteListUsersOnly = False
        self.ephemeralRes = ephemeralRes
        options = options = [
            discord.SelectOption(
                label="New Moons",
                value="new",
                emoji=lunarFilterMenuEmojis['new'],
                default=False,
            ),
            discord.SelectOption(
                label="Waxing Crescents",
                value="waxing_crescent",
                emoji=lunarFilterMenuEmojis['waxing_crescent'],
                default=False,
            ),
            discord.SelectOption(
                label="First Quarter",
                value="first_quarter",
                emoji=lunarFilterMenuEmojis['first_quarter'],
                default=False,
            ),
            discord.SelectOption(
                label="Waxing Gibbous'",
                value="waxing_gibbous",
                emoji=lunarFilterMenuEmojis['waxing_gibbous'],
                default=False,
            ),
            discord.SelectOption(
                label="Full Moons",
                value="full",
                emoji=lunarFilterMenuEmojis['full'],
                default=False,
            ),
            discord.SelectOption(
                label="Waning Gibbous'",
                value="waning_gibbous",
                emoji=lunarFilterMenuEmojis['waning_gibbous'],
                default=False,
            ),
            discord.SelectOption(
                label="Third Quarters",
                value="third_quarter",
                emoji=lunarFilterMenuEmojis['third_quarter'],
                default=False,
            ),
            discord.SelectOption(
                label="Waning Crescents",
                value="waning_crescent",
                emoji=lunarFilterMenuEmojis['waning_crescent'],
                default=False,
            ),
        ]
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

        phaseList = getPhaseList(
                    ephemeris,
                    filters = self.values,
                    useEmojis=useEmojis,
                    emojis=emojis,
                    )
        
        if phaseList[0] == "Range too Small":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateMoonCache((time.time() * 1000), numDisplayMoonCycles)
            phaseList = getPhaseList(
                ephemeris,
                filters= self.values,
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

