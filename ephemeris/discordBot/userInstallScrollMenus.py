from .commonImports import *
from .helperFuncs import *


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
            UserInstallScrollFilterMenu(
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

class UserInstallScrollFilterMenu(discord.ui.Select):
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

