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
    "White": "<:WhiteOrb:1294557088936362037>",
    "Black": "<:BlackOrb:1294556540937703434>",
    "Green": "<:GreenOrb:1294556773579227167>",
    "Red": "<:RedOrb:1294557034083258389>",
    "Purple": "<:PurpleOrb:1294556982732259400>",
    "Yellow": "<:YellowOrb:1294555945296203836>",
    "Cyan": "<:CyanOrb:1294556665005477939>",
    "Blue": "<:BlueOrb:1294556594595434547>"
}

lunarFilterMenuEmojis = {
    "new": "<:New:1294558070743109682>",
    "waxing_crescent": "<:WaxingCrescent:1294558192512270368>",
    "first_quarter": "<:FirstQuarter:1294558210388394057>",
    "waxing_gibbous": "<:WaxingGibbous:1294558273286045737>",
    "full": "<:Full:1294558315677745182>",
    "waning_gibbous": "<:WaningGibbous:1294558336657653841>",
    "third_quarter": "<:ThirdQuarter:1294558347785146370>",
    "waning_crescent": "<:WaningCrescent:1294558368400281633>"
}

# Change to the emojis you have uploaded to your bot's developer dashboard
defaultEmojis = {
    "White": "<:WhiteOrb:1294557088936362037>",
    "Black": "<:BlackOrb:1294556540937703434>",
    "Green": "<:GreenOrb:1294556773579227167>",
    "Red": "<:RedOrb:1294557034083258389>",
    "Purple": "<:PurpleOrb:1294556982732259400>",
    "Yellow": "<:YellowOrb:1294555945296203836>",
    "Cyan": "<:CyanOrb:1294556665005477939>",
    "Blue": "<:BlueOrb:1294556594595434547>",
    "new": "<:New:1294558070743109682>",
    "waxing_crescent": "<:WaxingCrescent:1294558192512270368>",
    "first_quarter": "<:FirstQuarter:1294558210388394057>",
    "waxing_gibbous": "<:WaxingGibbous:1294558273286045737>",
    "full": "<:Full:1294558315677745182>",
    "waning_gibbous": "<:WaningGibbous:1294558336657653841>",
    "third_quarter": "<:ThirdQuarter:1294558347785146370>",
    "waning_crescent": "<:WaningCrescent:1294558368400281633>",
    "lunation": "<a:Lunation:1294559206686462012>",
}

# user installs have the same emoji perms as the user using them
UsersInstallDefaultEmojis = {
    "new": "<:New:1294558070743109682>",
    "waxing_crescent": "<:WaxingCrescent:1294558192512270368>",
    "first_quarter": "<:FirstQuarter:1294558210388394057>",
    "waxing_gibbous": "<:WaxingGibbous:1294558273286045737>",
    "full": "<:Full:1294558315677745182>",
    "waning_gibbous": "<:WaningGibbous:1294558336657653841>",
    "third_quarter": "<:ThirdQuarter:1294558347785146370>",
    "waning_crescent": "<:WaningCrescent:1294558368400281633>"
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
