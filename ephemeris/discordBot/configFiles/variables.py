import json
from pathlib import Path

# Discord ID of the bot owner (only this user can update whitelist)
ownerID = 109931759260430336
# Triggers a few conditional statements when true
DEBUGGING = False

# Setting this to true will allow any user or guild to use bot and user app features regardless of their whitelist status
disableWhitelisting = False

# cache size and display range configuration
cacheStartDay = -4
cacheEndDay = 35
selectStartDay = -3
selectEndDay = 21
numMoonCycles = 8
numDisplayMoonCycles = 2
numFilterDisplayMoonCycles = 5
oneDay = 86400000

if DEBUGGING:
    cacheStartDay = -9
    selectStartDay = -9
    cacheEndDay = 2
    selectEndDay = 2

##############################################
# variables for using json files instead of DB
##############################################
# guildSettings = {}
# userSettings = {}
# guildWhiteList = {}
# userWhiteList = {}

# GSPath = Path("ephemeris/discordBot/configFiles/guildSettings.json").absolute()
# USPath = Path("ephemeris/discordBot/configFiles/userSettings.json").absolute()
# GWLPath = Path("ephemeris/discordBot/configFiles/guildWhiteList.json").absolute()
# UWLPath = Path("ephemeris/discordBot/configFiles/userWhiteList.json").absolute()

##############################################
# variables for using json files instead of DB
##############################################
# Create Files If they don't already exist
# if not GSPath.exists():
#     GSPath.write_text(json.dumps({}))
#     print(f"File created: {GSPath}")

# if not USPath.exists():
#     USPath.write_text(json.dumps({}))
#     print(f"File created: {USPath}")

# if not GWLPath.exists():
#     GWLPath.write_text(json.dumps({}))
#     print(f"File created: {GWLPath}")

# if not UWLPath.exists():
#     UWLPath.write_text(json.dumps({}))
#     print(f"File created: {UWLPath}")

# with GSPath.open("r") as f:
#     guildSettings = json.load(f)
# with USPath.open("r") as f:
#     userSettings = json.load(f)
# with GWLPath.open("r") as f:
#     guildWhiteList = json.load(f)
# with UWLPath.open("r") as f:
#     userWhiteList = json.load(f)

scrollFilterMenuEmojis = {
    "White": "<:WhiteOrb:998472151965376602>",
    "Black": "<:BlackOrb:998472215295164418>",
    "Green": "<:GreenOrb:998472231640379452>",
    "Red": "<:RedOrb:998472356303478874>",
    "Purple": "<:PurpleOrb:998472375400149112>",
    "Yellow": "<:YellowOrb:998472388406689812>",
    "Cyan": "<:CyanOrb:998472398707888229>",
    "Blue": "<:BlueOrb:998472411861233694>",
}

lunarFilterMenuEmojis = {
    "new": "<:New:1092364396602327050>",
    "waxing_crescent": "<:WaxingCrescent:1092364467712569395>",
    "first_quarter": "<:FirstQuarter:1092364360812347402>",
    "waxing_gibbous": "<:WaxingGibbous:1092364485337034792>",
    "full": "<:Full:1092364372652855397>",
    "waning_gibbous": "<:waningGibbous:1088075517799972934>",
    "third_quarter": "<:ThirdQuarter:1092364421113851955>",
    "waning_crescent": "<:WaningCrescent:1092364435986853928>",
}

# can use cross server emojis
defaultEmojis = {
    "White": "<:WhiteOrb:998472151965376602>",
    "Black": "<:BlackOrb:998472215295164418>",
    "Green": "<:GreenOrb:998472231640379452>",
    "Red": "<:RedOrb:998472356303478874>",
    "Purple": "<:PurpleOrb:998472375400149112>",
    "Yellow": "<:YellowOrb:998472388406689812>",
    "Cyan": "<:CyanOrb:998472398707888229>",
    "Blue": "<:BlueOrb:998472411861233694>",
    "new": "<:New:1092364396602327050>",
    "waxing_crescent": "<:WaxingCrescent:1092364467712569395>",
    "first_quarter": "<:FirstQuarter:1092364360812347402>",
    "waxing_gibbous": "<:WaxingGibbous:1092364485337034792>",
    "full": "<:Full:1092364372652855397>",
    "waning_gibbous": "<:WaningGibbous:1092364454479548456>",
    "third_quarter": "<:ThirdQuarter:1092364421113851955>",
    "waning_crescent": "<:WaningCrescent:1092364435986853928>",
    "lunation": "<a:moon:440289423750463488>",
}

# user installs have the same emoji perms as the user using them
UsersInstallDefaultEmojis = {
    "new": ":new_moon:",
    "waxing_crescent": ":waxing_crescent_moon:",
    "first_quarter": ":first_quarter_moon:",
    "waxing_gibbous": ":waxing_gibbous_moon:",
    "full": ":full_moon:",
    "waning_gibbous": ":waning_gibbous_moon:",
    "third_quarter": ":last_quarter_moon:",
    "waning_crescent": ":waning_crescent_moon:",
}

# text inserts for lunar menus
moonDisplayNames = {
    "new": "**New**",
    "waxing_crescent": "a **Waxing Crescent**",
    "first_quarter": "in its **First Quarter**",
    "waxing_gibbous": "a **Waxing Gibbous**",
    "full": "**Full**",
    "waning_gibbous": "a **Waning Gibbous**",
    "third_quarter": "in its **Third Quarter**",
    "waning_crescent": "a **Waning Crescent**",
}

# response message name inserts for filtered phases
moonFilterDisplayNames = {
    "new": "**New**",
    "waxing_crescent": "**Waxing Crescent**",
    "first_quarter": "**First Quarter**",
    "waxing_gibbous": "**Waxing Gibbous**",
    "full": "**Full**",
    "waning_gibbous": "**Waning Gibbous**",
    "third_quarter": "**Third Quarter**",
    "waning_crescent": "**Waning Crescent**",
}

lunarLabels = {
    # button labels for lunar menus
    "all": "All Moon Phases",
    "next_full": "Next Full Moon",
    "next_new": "Next New Moon",
    "current": "Current Phase",
    # select menu labels for lunar menus
    "new": "New Moons",
    "waxing_crescent": "Waxing Crescents",
    "first_quarter": "First Quarters",
    "waxing_gibbous": "Waxing Gibbous'",
    "full": "Full Moons",
    "waning_gibbous": "Waning Gibbous'",
    "third_quarter": "Third Quarters",
    "waning_crescent": "Waning Crescents",
}

# key: current phase, value: previous phase from key
previousPhases = {
    "new": "waning_crescent",
    "waxing_crescent": "new",
    "first_quarter": "waxing_crescent",
    "waxing_gibbous": "first_quarter",
    "full": "waxing_gibbous",
    "waning_gibbous": "full",
    "third_quarter": "waning_gibbous",
    "waning_crescent": "third_quarter",
}

# embed thumbnail images
scrollThumbnailURL = "https://i.imgur.com/Lpa96Ry.png"
moonThumbnailURL = "https://imgur.com/rzm8JUj.gif"
