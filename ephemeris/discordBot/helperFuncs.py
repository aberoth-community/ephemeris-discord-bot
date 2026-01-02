from num2words import num2words
from .commonImports import *
from .configFiles.usageDataBase import log_usage_event


def is_owner(interaction: discord.Interaction) -> bool:
    """Checks if the user that triggered the interaction is the bot owner"""
    return interaction.user.id == ownerID


async def not_owner_error(interaction: discord.Interaction, error):
    """Handles the interaction response when the user that triggered the interaction
    is not the bot owner"""
    if isinstance(error, discord.app_commands.errors.CheckFailure):
        await interaction.response.send_message(
            content=f"Only the bot owner (<@{ownerID}>) may use this command",
            ephemeral=True,
        )


def log_usage(
    interaction: discord.Interaction,
    feature: str,
    action: str,
    context=None,
    details=None,
) -> None:
    if not ENABLE_USAGE_LOGGING:
        return
    if isinstance(context, (list, tuple, set)):
        context = ",".join(str(item) for item in context)
    try:
        log_usage_event(
            interaction=interaction,
            feature=feature,
            action=action,
            context=context,
            details=details,
        )
    except Exception:
        pass


def getDayList(
    ephemeris: Ephemeris,
    startDay: int,
    useEmojis: bool = False,
    filters: list[str] = None,
    emojis: dict = None,
    endDay: int = None,
):
    """Subsections ephemeris.scrollEventsCache in order to filter out the user selected events.
    Combines the events' information into a single string.

    Parameters
    ---------
        ephemeris: `Ephemeris`
            An instance of the Ephemeris class.
        startDay: `int`
            The number of days from the current time that that the earliest event in can start
            at within the filtered events.
        filters: `list[str]`
            A `list` containing the phases that should be filtered for.
        useEmojis: `bool` *optional*
            When set to true the message line will use emojis instead of the text name for orbs
            that are affected by the event. Defaults to True.
        emojis: `dict[str,str]` *optional*
            A `dict` with orb names for keys and string containing a discord emoji for its values. Defaults to None.
        endDay: `int`
            The number of days from the current time that that the latest event in can start
            at within the filtered events.
    Returns
    ---------
        `str`
            A multi-line string describing the phase changes for a preset number of cycles from startTime.
    """
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
    if end >= ephemeris.scrollEventsCache[-1][0]:
        return ["Out of Range"]
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


def getPhaseList(
    ephemeris: Ephemeris,
    startTime: int = None,
    filters: dict[str, str] = None,
    useEmojis: bool = False,
    emojis: dict[str, str] = None,
    firstEventOnly: bool = False,
) -> str:
    """Subsections ephemeris.moonCyclesCache in order to filter out the user selected events.
    Combines the events' information into a single string.

    Parameters
    ---------
        ephemeris: `Ephemeris`
            An instance of the Ephemeris class.
        startTime: `int`
            An epoch timestamp in ms that represents the earliest time an event can start at within
            the filtered events.
        filters: `dict[str,str]`
            A `dict` containing the phases that should be filtered for.
        useEmojis: `bool` *optional*
            When set to true the message line will use emojis instead of the text name for orbs
            that are affected by the event. Defaults to True.
        firstEventOnly: `bool` *optional*
            Indicates that only information from the first of the filtered events should returned. Defaults to False.
        emojis: `dict[str,str]` *optional*
            A `dict` with orb names for keys and string containing a discord emoji for its values. Defaults to None.

    Returns
    ---------
        `str`
            A multi-line string describing the phase changes for a preset number of cycles from startTime.
    """
    start = startTime
    firstLine = ""
    if start == None:
        currentTime = round((time.time() * 1000))
        start = currentTime - ephemeris.oneAberothDay

    startIndex = next(
        (
            i
            for i, (timestamp, _) in enumerate(ephemeris.moonCyclesCache)
            if timestamp > start
        ),
        None,
    )

    # filterLabelsToEventName = {
    #     lunarLabels["all"]: "all",
    #     lunarLabels["current"]: "current",
    #     lunarLabels["nextFull"]: "full",
    #     lunarLabels["nextNew"]: "nextNew",
    #     lunarLabels["new"]: ""
    #     }

    firstFilters = {"next_full": "full", "next_new": "new"}
    # eventFilters = [firstFilters[phase] if phase in firstFilters else phase
    #                  for (phase, label) in lunarLabels.items() if label in filters]
    eventFilters = []
    for phase, label in lunarLabels.items():
        if label in filters or phase in filters:
            if phase == "next_new":
                phase = "new"
            elif phase == "next_full":
                phase = "full"
            eventFilters.append(phase)

    displayingCurrent = False
    subCache = []
    if startIndex != None:
        if eventFilters != None and len(eventFilters) != 0:
            if "all" in eventFilters:
                subCache = ephemeris.moonCyclesCache[startIndex:]
                if len(subCache) < numDisplayMoonCycles * 8 + 1:
                    return ["Range too Small"]
                else:
                    subCache = subCache[: numDisplayMoonCycles * 8 + 1]
                    firstLine = f"__**Next {num2words(numDisplayMoonCycles).capitalize()} Aberoth Synodic Months:**__"
            elif "current" in eventFilters:
                displayingCurrent = True
                subCache = [copy.deepcopy(ephemeris.moonCyclesCache[startIndex])]
                # if the phase at the start index is the next phase
                if subCache[0][0] > currentTime:
                    # we already have the next time now we need to get the phase for current phase
                    subCache[0][1]["phase"] = previousPhases[subCache[0][1]["phase"]]
                # check if there is another event in the moonCycle cache to find end of current event
                elif len(ephemeris.moonCyclesCache[startIndex:]) < 2:
                    return ["Range too Small"]
                # if current phase is a 1 night phase it can appear at the start index of moonCyclesCache
                # in this case we have the current phase already but not the end time
                else:
                    subCache[0][1]["discordTS"] = ephemeris.moonCyclesCache[
                        startIndex + 1
                    ][1]["discordTS"]
                firstLine = "__**Current Phase:**__"
            elif firstEventOnly:
                subCache = [
                    next(
                        (
                            event
                            for event in ephemeris.moonCyclesCache[startIndex:]
                            if event[1]["phase"] in eventFilters
                        ),
                        None,
                    )
                ]
                firstLine = f"__**Next {(subCache[0][1]['phase']).capitalize()} Moon:**__\n*Note: phase may be the current phase.*"
            else:
                subCache = [
                    event
                    for event in ephemeris.moonCyclesCache[startIndex:]
                    if event[1]["phase"] in eventFilters
                ]
                if len(subCache) < numFilterDisplayMoonCycles * len(eventFilters):
                    return ["Range too Small"]
                else:
                    subCache = subCache[: numFilterDisplayMoonCycles * 8 + 1]
                    firstLine = f"__**Filtered Phases:**__\nNext {join_with_oxford_comma(eventFilters)} moons over the next {num2words(numFilterDisplayMoonCycles)} Aberoth synodic months"
    if len(subCache) < 1:
        return ["Range too Small"]

    eventMsg = firstLine
    for event in subCache:
        eventMsg += "\n" + createLunarEventMsgLine(
            event, useEmojis, emojis=emojis, displayingCurrent=displayingCurrent
        )
    return eventMsg


def createLunarEventMsgLine(
    event: tuple[int, dict[str, str]],
    useEmojis: bool = True,
    emojis: dict[str, str] = None,
    displayingCurrent: bool = False,
) -> str:
    """Creates a one line string that describes the new phase phase that starts at the event time.

    Parameters
    ---------
        event: `tuple[int, dict[str, any]]`
            The event that the message line provides information about.
        useEmojis: `bool` *optional*
            When set to true the message line will use the user's set emojis instead of the default emojis
            for phase at the event time. Defaults to True.
        emojis: `dict[str,str]` *optional*
            A `dict` with orb names for keys and string containing a discord emoji for its values. Defaults to None.
        displayingCurrent: `bool` *optional*
            Indicates whether or not the event is for the current phase. Defaults to False.

    Returns
    ---------
        `str`
            A one line string that describes the phase at the time for the passed in event.
    """
    if useEmojis and emojis != None:
        if displayingCurrent:
            return f"> {emojis[event[1]['phase']]} the moon is {moonDisplayNames[event[1]['phase']]} until {event[1]['discordTS']}."
        else:
            return f"> {emojis[event[1]['phase']]} {event[1]['discordTS']} the moon is {moonDisplayNames[event[1]['phase']]}."
    else:
        if displayingCurrent:
            return f"> {UsersInstallDefaultEmojis[event[1]['phase']]} the moon is {moonDisplayNames[event[1]['phase']]} until {event[1]['discordTS']}."
        else:
            return f"> {UsersInstallDefaultEmojis[event[1]['phase']]} {event[1]['discordTS']} {moonDisplayNames[event[1]['phase']]}."


def createScrollEventMsgLine(
    event: tuple, useEmojis=True, firstEvent=False, emojis=None
) -> str:
    """Creates a one line string that describes the changes in orb states at the event.

    Parameters
    ---------
        event: `tuple[int, dict[str, any]]`
            The event that the message line provides information about.
        useEmojis: `bool` *optional*
            When set to true the message line will use emojis instead of the text name for orbs
            that are affected by the event. Defaults to True.
        firstEvent: `bool` *optional*
            Indicates that the passed in event is the first line in the message so formatting can be
            adjusted accordingly. Defaults to False.
        emojis: `dict[str,str]` *optional*
            A `dict` with orb names for keys and string containing a discord emoji for its values. Defaults to None.

    Returns
    ---------
        `str`
            A one line string that describes the scroll event changes for the passed in events
    """
    glows = event["newGlows"]
    darks = [i for i in event["newDarks"] if i != "Shadow"]
    normals = [i for i in event["returnedToNormal"] if i != "Shadow"]
    msg = f"> {event['discordTS']}"
    for index, cat in enumerate([glows, darks, normals]):
        tempMsg = ""
        if len(cat) < 1:
            # only one item in the category has changed
            continue
        elif len(cat) >= 3:
            # over 3 in the category needs an oxford comma
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
            # just two in the category only needs an and
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


def splitMsg(msg: str, maxLen: int = 2000) -> list[str]:
    """Splits a message into a `list` of strings. Splits on the previous new line
    character when the length of current string exceeds the value of maxLen.

    Parameters
    ---------
        msg: `str`
            The message to be split.

    Returns
    ---------
        `list[str]`
            An ordered `list` of strings with length less than maxLen.
    """
    msgArr = []
    while len(msg) > maxLen:
        # find last index in range
        i = msg[:2000].rfind("\n")
        msgArr.append(msg[:i])
        msg = msg[i:]
    msgArr.append(msg)
    return msgArr


# functions for using json files instead of DB
# def updateSettings(settings, settingsFile:Path=GSPath):
#     json_object = json.dumps(settings, indent=4)
#     with open(settingsFile, "w") as outfile:
#         outfile.write(json_object)

# def getSettings(settingsFile:Path=GSPath):
#     settings = {}
#     with open(settingsFile, "r") as json_file:
#         settings = json.load(json_file)
#     return settings


def isEmoji(emojiStr: str) -> bool:
    """Checks if the argument is an emoji.

    Parameters
    ---------
        emojiStr: `str`
            The string to check if it's an emoji
    Returns
    ---------
        `bool`
            True if string is an emoji, False if string is not an emoji.
    """
    if bool(match(r"\p{Emoji}", emojiStr)):
        return True
    if len(emojiStr) < 5:
        return False
    if emojiStr[:2] + emojiStr[-1] == "<:>" or emojiStr[0] + emojiStr[-1] == "::":
        return True
    else:
        return False


def join_with_oxford_comma(items: list) -> str:
    """Joins a list with using an oxford comma when needed.

    Parameters
    ---------
        items: `list`
            A list of strings to be joined.
    Returns
    ---------
        `str`
        A string with the elements in items joined by a comma/oxford comma or and in the case of two elements.
    """
    phaseNames = [moonFilterDisplayNames[item] for item in items]

    # Handle different lengths
    if len(phaseNames) == 0:
        return ""  # Return empty string if list is empty
    elif len(phaseNames) == 1:
        return phaseNames[0]  # Return single item if only one element
    elif len(phaseNames) == 2:
        return " and ".join(phaseNames)  # Join with "and" if two elements
    else:
        # Join with commas and an Oxford comma for three or more elements
        return ", ".join(phaseNames[:-1]) + ", and " + phaseNames[-1]


def checkWhiteListed(
    interaction: discord.Interaction,
    guildSettings: dict,
    userSettings: dict,
    whiteListUsersOnly: bool = True,
) -> bool:
    """Checks if the user is white listed to use menus in the settings database.

    Parameters
    ---------
        interaction: `discord.Interaction`
            The interaction that the white list permissions need to be checked for.
        guildSettings: `dict`
            The settings for the guild that the interaction ocurred in.
        userSettings: `dict`
            The settings for the user that triggered the interaction.
        whiteListUsersOnly: `bool` *optional*.
            True if only white listed users are allowed to complete the interaction request. Defaults to True.

    Returns
    ---------
        `bool`
        True if the user and guild pass the white check.
    """
    exp = 0
    if 0 in interaction._integration_owners:
        exp = guildSettings["expiration"]
    whiteListed = True if exp == -1 else exp > time.time()
    if whiteListUsersOnly:
        temp = (
            True
            if userSettings["expiration"] == -1
            else userSettings["expiration"] > time.time()
        )
        whiteListed = whiteListed and temp
    elif 1 in interaction._integration_owners:
        whiteListed = (
            True
            if userSettings["expiration"] == -1
            else userSettings["expiration"] > time.time()
        )
    return whiteListed


def formatTime(milliseconds: int) -> str:
    """Takes in a length of time in milliseconds and formats it into h:m:s format

    Parameters
    ---------
        milliseconds: `int`
            The lenght of time to be formatted
    Returns
    ---------
        `str`
        The length of time in the format f"{hours:.0f}h {minutes:.0f}m {seconds:.2f}s"
    """
    # Convert milliseconds to seconds
    seconds = milliseconds // 1000
    # Calculate hours, minutes and seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # Return formatted time string
    return f"{hours:.0f}h {minutes:.0f}m {seconds:.2f}s"
