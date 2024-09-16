from .commonImports import *
from .helperFuncs import splitMsg, getPhaseList

# Create seperate menu that will persist
class UserInstallLunarMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=False,
        timeout=300,
        whiteListUsersOnly = False,
        emojis=None,
        useEmojis = False
    ):
        super().__init__(timeout=timeout)
        self.ephemeralRes = ephemeralRes
        self.whiteListUsersOnly = whiteListUsersOnly
        self.emojis=emojis
        self.useEmojis = useEmojis
        self.add_item(UserInstallPhaseSelMenu(
            whiteListUsersOnly=whiteListUsersOnly,
            ephemeralRes=ephemeralRes,
            useEmojis=useEmojis,
            emojis=emojis))

    @discord.ui.button(
        label=lunarLabels["all"], style=discord.ButtonStyle.green, emoji=defaultEmojis['lunation']
    )
    async def allPhases(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.UserInstallLunarMenuBtnPress(interaction=interaction, button=button)

    @discord.ui.button(
        label=lunarLabels['next_full'], style=discord.ButtonStyle.primary, emoji=defaultEmojis['full']
    )
    async def fullMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.UserInstallLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
        
    @discord.ui.button(
        label=lunarLabels['next_new'], style=discord.ButtonStyle.grey, emoji=defaultEmojis['new']
    )
    async def newMoon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.UserInstallLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
        
    @discord.ui.button(
        label=lunarLabels['current'], style=discord.ButtonStyle.grey, emoji='❔'
    )
    async def currentPhase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.UserInstallLunarMenuBtnPress(interaction=interaction, button=button, firstEventOnly=True)
    
    async def UserInstallLunarMenuBtnPress(self, interaction: discord.Interaction, button: discord.ui.Button, firstEventOnly:bool = False):
        userSettings = fetch_user_settings(interaction.user.id)
        whiteListed = True
        messageDefered = False
        if self.whiteListUsersOnly:
            exp = userSettings.get('expiration')
            whiteListed = True if exp == -1 else exp > time.time()
        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return
                
        phaseList = getPhaseList(
                        ephemeris,
                        filters = [button.label],
                        useEmojis=self.useEmojis,
                        emojis=self.emojis,
                        firstEventOnly=firstEventOnly
                        )
        
        if phaseList[0] == "Range too Small":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateMoonCache((time.time() * 1000), numDisplayMoonCycles)
            phaseList = getPhaseList(
                ephemeris,
                filters=[button.label],
                useEmojis=self.useEmojis,
                emojis=self.emojis,
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

class UserInstallPhaseSelMenu(discord.ui.Select):
    def __init__(
        self, 
        ephemeralRes=True,
        whiteListUsersOnly=False,
        emojis=None,
        useEmojis = False
    ):
        self.whiteListUsersOnly = whiteListUsersOnly
        self.ephemeralRes = ephemeralRes
        self.emojis = emojis
        self.useEmojis = useEmojis
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
        userSettings = fetch_user_settings(interaction.user.id)
        whiteListed = True
        messageDefered = False
        if self.whiteListUsersOnly:
            exp = userSettings.get('expiration')
            whiteListed = True if exp == -1 else exp > time.time()
        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**User does not have permission to use this menu.**\nType `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permsissions` for more information.",
                ephemeral=True,
            )
            return

        phaseList = getPhaseList(
                    ephemeris,
                    filters = self.values,
                    useEmojis=self.useEmojis,
                    emojis=self.emojis,
                    )
        
        if phaseList[0] == "Range too Small":
            await interaction.response.defer(ephemeral=self.ephemeralRes, thinking=True)
            messageDefered = True
            ephemeris.updateMoonCache((time.time() * 1000), numDisplayMoonCycles)
            phaseList = getPhaseList(
                ephemeris,
                filters= self.values,
                useEmojis=self.useEmojis,
                emojis=self.emojis,
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
            # if the number of responses will reach the max for DMs (messages aren't sent in a guild)
            if len(msgArr) > 6 and 0 in interaction._integration_owners:
                for msg in msgArr[1:6]:
                    await interaction.followup.send(
                        content=msg, ephemeral=self.ephemeralRes
                    )
                msg = "**Maximum number of follow ups reached for private message!**\nPlease use a smaller filter"
                await interaction.followup.send(
                        content=msg, ephemeral=self.ephemeralRes
                    )
            else:    
                for msg in msgArr[1:]:
                    await interaction.followup.send(
                        content=msg, ephemeral=self.ephemeralRes
                    )

