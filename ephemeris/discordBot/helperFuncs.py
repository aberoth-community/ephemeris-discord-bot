from num2words import num2words
from .commonImports import *

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == ownerID

async def not_owner_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.CheckFailure):
        await interaction.response.send_message(
                    content=f"Only the bot owner (<@{ownerID}>) may use this command",
                    ephemeral=True,
                )

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

def getPhaseList(ephemeris:Ephemeris, startTime:int = None, filters:dict = None, useEmojis:bool=False, emojis:dict=None, firstEventOnly:bool=False):
    start = startTime
    firstLine = ''
    if start == None:
        currentTime = round((time.time() * 1000))
        start = currentTime - ephemeris.oneAberothDay
    
    startIndex = next((i for i, (timestamp, _) in enumerate(ephemeris.moonCyclesCache) if timestamp > start), None)
    
    # filterLabelsToEventName = {
    #     lunarLabels["all"]: "all",
    #     lunarLabels["current"]: "current",
    #     lunarLabels["nextFull"]: "full",
    #     lunarLabels["nextNew"]: "nextNew",
    #     lunarLabels["new"]: ""
    #     }
    
    firstFilters = {'next_full': 'full', 'next_new': "new"}
    # eventFilters = [firstFilters[phase] if phase in firstFilters else phase
    #                  for (phase, label) in lunarLabels.items() if label in filters]
    eventFilters = []
    for (phase, label) in lunarLabels.items():
        if label in filters or phase in filters:
            if phase == 'next_new':
                phase = 'new'
            elif phase == 'next_full':
                phase = 'full'
            eventFilters.append(phase)

    displayingCurrent = False
    subCache = []
    if startIndex:
        if eventFilters != None and len(eventFilters) != 0:
            if 'all' in eventFilters:
                subCache = ephemeris.moonCyclesCache[startIndex:]
                if len(subCache) < numDisplayMoonCycles * 8 + 1:
                    return ['Range too Small']
                else: 
                    subCache = subCache[:numDisplayMoonCycles * 8 + 1]
                    firstLine = f"__**Next {num2words(numDisplayMoonCycles)} Aberoth Syndonic Months:**__"
            elif 'current' in eventFilters:
                displayingCurrent = True
                subCache = [copy.deepcopy(ephemeris.moonCyclesCache[startIndex])]
                # if the phase at the start index is the next phase
                if subCache[0][0] > currentTime:
                    # we already have the next time now we need to get the phase for current phase
                    subCache[0][1]['phase'] = previousPhases[subCache[0][1]['phase']]
                # check if there is another event in the moonCycle cache to find end of current event
                elif len(ephemeris.moonCyclesCache[startIndex:]) < 2:
                    return ['Range too Small']
                # if current phase is a 1 night phase it can appear at the start index of mooncyclesCache
                # in this case we have the current phase already but not the end time
                else: 
                    subCache[0][0] = ephemeris.moonCyclesCache[startIndex+1][0]
                firstLine = "__**Current Phase:**__"
            elif firstEventOnly:
                subCache = [next((event for event in ephemeris.moonCyclesCache[startIndex:] if event[1]['phase'] in eventFilters), None)]
                firstLine = f"__**Next {(subCache[0][1]['phase']).capitalize()} Moon:**__\n*Note: phase may be the current phase.*"
            else:
                subCache = [event for event in ephemeris.moonCyclesCache[startIndex:] if event[1]['phase'] in eventFilters]
                if len(subCache) < numFilterDisplayMoonCycles * len(eventFilters):
                    return ['Range too Small']
                else: 
                    subCache = subCache[:numFilterDisplayMoonCycles * 8 + 1]
                    firstLine = f"__**Filtered Phases:**__\nNext {join_with_oxford_comma(eventFilters)} moons over the next {num2words(numFilterDisplayMoonCycles)} Aberoth syndonic months"
    if len(subCache) < 1:
        return ['Range too Small']
    
    eventMsg = firstLine
    for event in subCache:
        eventMsg += "\n" + createLunarEventMsgLine(event, useEmojis, emojis=emojis, displayingCurrent=displayingCurrent)
    return eventMsg

def createLunarEventMsgLine(event:tuple[int, dict[str, str]], useEmojis:bool=True, emojis:dict=None, displayingCurrent:bool=False) -> str:
    if useEmojis and emojis != None:
        if displayingCurrent:
            return f"> {emojis[event[1]['phase']]} the moon is {moonDisplayNames[event[1]['phase']]} until {event[1]['discordTS']}."
        else: return f"> {emojis[event[1]['phase']]} {event[1]['discordTS']} the moon is {moonDisplayNames[event[1]['phase']]}."
    else:
        if displayingCurrent:
            return f"> {defaultEmojis[event[1]['phase']]} the moon is {moonDisplayNames[event[1]['phase']]} until {event[1]['discordTS']}."
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
        emojiStr (str): the string to check if it's an emoji

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

def join_with_oxford_comma(items):
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