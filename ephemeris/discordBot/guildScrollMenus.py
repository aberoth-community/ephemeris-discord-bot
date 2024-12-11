from threading import Timer
from asyncio import run_coroutine_threadsafe
from .commonImports import *
from .helperFuncs import *
from .configFiles.dataBase import (
    update_guild_settings,
    update_user_settings,
    fetch_guild_settings,
    fetch_user_settings,
)


class GuildScrollMenu(discord.ui.View):
    def __init__(
        self,
        ephemeralRes=True,
        timeout=None,
        allow_filters=None,
        filterOptions=None,
        filterList=None,
        setUp=True,
        filterResetTimer = {}
    ):
        super().__init__(timeout=timeout)
        self.setUp = setUp
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        self.allow_filters = allow_filters
        self.whiteListUsersOnly = False
        self.filterResetTimer = filterResetTimer
        self.add_item(GuildDaySelMenu(filterList=filterList, setUp=self.setUp, ephemeralRes=ephemeralRes, filterResetTimer=filterResetTimer))
        if self.allow_filters == 1:
            self.add_item(GuildFilterMenu(filterOptions, filterResetTimer=filterResetTimer))

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
    async def tomorrow(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.guildScrollMenuBtnPress(interaction=interaction, button=button)

    async def guildScrollMenuBtnPress(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guildSettings = fetch_guild_settings(interaction.guild_id)
        if not guildSettings:
            guildSettings = newGuildSettings(interaction, useEmojis)
            update_guild_settings(interaction.guild_id, guildSettings)
        userSettings = fetch_user_settings(interaction.user.id)
        if not userSettings:
            userSettings = newUserSettings(interaction.user.id, interaction.user.name)
            update_user_settings(interaction.user.id, userSettings)
        whiteListed = False
        messageDeferred = False

        useEmojis = False
        emojis = None
        if guildSettings["channels"][str(interaction.channel_id)]["useEmojis"] == 1:
            useEmojis = True
            emojis = guildSettings["emojis"]
        if (
            guildSettings["channels"][str(interaction.channel_id)][
                "whitelisted_users_only"
            ]
            == 1
        ):
            self.whiteListUsersOnly = True
        if self.setUp == False:
            # Assigns menu state on interaction when bot is restarted
            self.setUp = True
            self.filterList = guildSettings["channels"][
                str(interaction.channel_id)
            ].get("filters")

        whiteListed = checkWhiteListed(
            interaction, guildSettings, userSettings, self.whiteListUsersOnly
        )

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permissions` for more information.",
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
            messageDeferred = True
            ephemeris.updateScrollCache(
                start=(time.time() * 1000) + cacheStartDay * oneDay,
                stop=(time.time() * 1000) + cacheEndDay * oneDay,
            )
            dayList = getDayList(
                ephemeris,
                startDay=startDays[button.label],
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )

        msgArr = splitMsg(dayList)
        
        self.filterResetTimer = create_or_reset_filter_timer(self.filterResetTimer,
                                                             UpdateViewAfterTimer,
                                                             interaction.client.loop,
                                                             interaction)
        
        if messageDeferred:
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


class GuildDaySelMenu(discord.ui.Select):
    def __init__(
        self, ephemeralRes=True, filterList=None, setUp=False, whiteListUsersOnly=False,  filterResetTimer={}
    ):
        self.setUp = setUp
        self.whiteListUsersOnly = False
        self.ephemeralRes = ephemeralRes
        self.filterList = filterList
        self.filterResetTimer =  filterResetTimer
        options = [
            discord.SelectOption(label=x)
            for x in range(selectStartDay, selectEndDay + 1)
        ]
        super().__init__(
            placeholder="Select how many days from today",
            options=options,
            custom_id="selectDay",
            min_values=1,
            max_values=2,
        )

    async def callback(self, interaction: discord.Interaction):
        guildSettings = fetch_guild_settings(interaction.guild_id)
        if not guildSettings:
            guildSettings = newGuildSettings(interaction, useEmojis)
            update_guild_settings(interaction.guild_id, guildSettings)
        userSettings = fetch_user_settings(interaction.user.id)
        if not userSettings:
            userSettings = newUserSettings(interaction.user.id, interaction.user.name)
            update_user_settings(interaction.user.id, userSettings)
        whiteListed = False
        messageDeferred = False

        useEmojis = False
        emojis = None
        if guildSettings["channels"][str(interaction.channel_id)]["useEmojis"] == 1:
            useEmojis = True
            emojis = guildSettings["emojis"]
        if (
            guildSettings["channels"][str(interaction.channel_id)][
                "whitelisted_users_only"
            ]
            == 1
        ):
            self.whiteListUsersOnly = True
        if self.setUp == False:
            # Assign menu state on interaction when bot is restarted
            self.setUp = True
            self.filterList = guildSettings["channels"][
                str(interaction.channel_id)
            ].get("filters")

        whiteListed = checkWhiteListed(
            interaction, guildSettings, userSettings, self.whiteListUsersOnly
        )

        if not whiteListed and not disableWhitelisting:
            await interaction.response.send_message(
                content="**Server or user does not have permission to use this command.**\nUse `/permissions` for more information.",
                ephemeral=True,
            )
            return

        start = min(map(int, self.values))
        end = max(map(int, self.values))
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
            messageDeferred = True
            ephemeris.updateScrollCache(
                start=(time.time() * 1000) + cacheStartDay * oneDay,
                stop=(time.time() * 1000) + cacheEndDay * oneDay,
            )
            dayList = dayList = getDayList(
                ephemeris,
                startDay=start,
                endDay=end,
                filters=self.filterList,
                useEmojis=useEmojis,
                emojis=emojis,
            )
        msgArr = splitMsg(dayList)
        
        self.filterResetTimer = create_or_reset_filter_timer(self.filterResetTimer,
                                                             UpdateViewAfterTimer,
                                                             interaction.client.loop,
                                                             interaction)
        
        if messageDeferred:
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

        # update_guild_settings(interaction.guild_id, guildSettings)


class GuildFilterMenu(discord.ui.Select):
    def __init__(self, filterOptions=None, timeout=None, filterResetTimer={}):
        self.timeout = timeout
        if filterOptions == None:
            filterOptions = {
                "White": True,
                "Black": True,
                "Green": True,
                "Red": True,
                "Purple": True,
                "Yellow": True,
                "Cyan": True,
                "Blue": True,
            }
        self.filterResetTimer = filterResetTimer
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
        guildSettings = fetch_guild_settings(interaction.guild_id)
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
        guildSettings["channels"][str(interaction.channel_id)]["filters"] = filterList
        update_guild_settings(interaction.guild_id, guildSettings)
        
        self.filterResetTimer = create_or_reset_filter_timer(self.filterResetTimer,
                                                             UpdateViewAfterTimer,
                                                             interaction.client.loop,
                                                             interaction)
            
        # change select menu options
        await interaction.response.edit_message(
            view=GuildScrollMenu(
                timeout=None,
                filterOptions=filterOptions,
                filterList=filterList,
                allow_filters=1,
                filterResetTimer=self.filterResetTimer
            )
        )

class AsyncTimer:
    def __init__(self, interval, callback, loop, *args, **kwargs):
        self.interval = interval
        self.callback = callback
        self.loop = loop
        self.args = args
        self.kwargs = kwargs
        self.timer = None

    def start(self):
        self.timer = Timer(self.interval, self._runCallback)
        self.timer.start()

    def _runCallback(self):
        # runs the callback in the asyncio event loop.
        run_coroutine_threadsafe(self.callback(*self.args, **self.kwargs), self.loop)

    def reset(self):
        # current_time = datetime.now().strftime("%H:%M:%S")
        # print(f"Resetting Current time: {current_time}")
        self.cancel()
        self.start()

    def cancel(self):
        if self.timer:
            self.timer.cancel()

# Updates the view after the timer ends
async def UpdateViewAfterTimer(interaction) -> None:
    # using default arguments sets filter to default filters
    await interaction.message.edit(
        view=GuildScrollMenu(
            allow_filters=1,
        )
    )

def create_or_reset_filter_timer(timer, callback, loop, interaction, interval=filterResetTime, startOnCreate=True) -> None:
    if timer:
        # reset the existing timer
        timer.reset()
        # print("reset")
    else:
        # create a new timer if none exists
        # print("creating new timer")
        timer = AsyncTimer(
            interval, 
            callback, 
            loop,
            interaction
        )
        timer.start()
    return timer
