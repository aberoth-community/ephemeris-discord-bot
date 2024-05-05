import time
import json
import discord
from discord import app_commands
from discord.ext import commands
from src.Ephemeris import Ephemeris

guildSettings = {}
guildWhiteList = {}
userWhiteList = {}
with open('src\\discordBot\\guildSettings.json') as f:
    guildSettings = json.load(f)
with open('src\\discordBot\\guildWhiteList.json') as f:
    guildWhiteList = json.load(f)
with open('src\\discordBot\\userWhiteList.json') as f:
    userWhiteList = json.load(f)
    
emojis = {
        "White": "<:WhiteOrb:998472151965376602>",
        "Black": "<:BlackOrb:998472215295164418>",
        "Green": "<:GreenOrb:998472231640379452>",
        "Red": "<:RedOrb:998472356303478874>",
        "Purple": "<:PurpleOrb:998472375400149112>",
        "Yellow": "<:YellowOrb:998472388406689812>",
        "Cyan": "<:CyanOrb:998472398707888229>",
        "Blue": "<:BlueOrb:998472411861233694>"
        }   
    
thumbnailURL = 'https://i.imgur.com/Lpa96Ry.png'
oneDay = 86400000
ephemeris = Ephemeris.Ephemeris(start=(time.time()*1000)-2*86400000, end=(time.time()*1000)+16*86400000)

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix='', intents=intents)
    async def setup_hook(self) -> None:
        self.add_view(GuildMenu())
        
bot = PersistentViewBot()
        
@bot.event
async def on_ready():
    print('Bot is up and ready!')
    try:
        synched = await bot.tree.sync()
        print(f"synched {len(synched)} command(s)")
    except Exception as e:
        print(e)

####################
#    COMMANDS
####################   
@bot.tree.command(name='hello')
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!", ephemeral=True)

@bot.tree.command(name="prediction_menu", description="Creates predictions menu. All users will be able to use the menu. Has a timeout.")
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def userInstallMenu(interaction: discord.Interaction):
    ephRes = False
    if str(interaction.user.id) not in userWhiteList:
            await interaction.response.send_message(content='You do not have permission to use this command', ephemeral=True)
            return
    embed = discord.Embed(title='**Select what day you would like the scroll events for**',
                          description='*Glows should be accurate within a minute*',
                          color=0xA21613)
    embed.add_field(name="**__Options:__**",
                    value=
                    "​\n**``Yesterday:``**\n```Returns all scroll events between now and 24 hours ago.```"
                    "\n**``Today:    ``**\n```Returns all scroll events between 6 hours ago and 24 hours from now.```"
                    "\n**``Tomorrow: ``**\n```Returns all scroll events between 24 hours from now to 48 hours from now.```"
                    "\n**``Later:    ``**\n```Use the drop down menu to select what day from now you'd like the scroll events for.```",
                    inline=False
    )
    embed.set_thumbnail(url=thumbnailURL)
    embed.set_footer(text='⏱️ Menu expires in five minutes')
    await interaction.response.send_message(embed=embed, view=MenuNoPersist(), ephemeral=False)

@bot.tree.command(name='create_persistent_menu', description="Creates prediction menu with no timeout. Requires admin. All users will be able to use interface.")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.default_permissions()
@app_commands.describe(use_emojis='Whether or not responses use emojis for orb names')
@app_commands.choices(use_emojis=[discord.app_commands.Choice(name='Yes', value=1), discord.app_commands.Choice(name='No', value=0)])
async def guildMenu(interaction: discord.Interaction, use_emojis: discord.app_commands.Choice[int]):
    ephRes = True
    if str(interaction.guild_id) not in guildWhiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
    guildSettings[str(interaction.guild_id)] = {"useEmojis": use_emojis.value}
    updateGuildSettings(settings=guildSettings)
    embed = discord.Embed(title='**Select what day you would like the scroll events for**',
                          description='*Glows should be accurate within a minute*',
                          color=0xA21613)
    embed.add_field(name="**__Details:__**",
                    value=
                    "​\n**``Yesterday:``**\n```Returns all scroll events between now and 24 hours ago.```"
                    "\n**``Today:    ``**\n```Returns all scroll events between 6 hours ago and 24 hours from now.```"
                    "\n**``Tomorrow: ``**\n```Returns all scroll events between 24 hours from now to 48 hours from now.```"
                    "\n**``Later:    ``**\n```Use the drop down menu to select what day from now you'd like the scroll events for.```",
                    inline=False
    )
    embed.set_thumbnail(url=thumbnailURL)
    await interaction.response.send_message(embed=embed, view = GuildMenu(), ephemeral=False)

####################
#      Menus
#################### 
class SelectMenuPersist(discord.ui.Select):
    def __init__(self, ephemeralRes=True):
        self.ephemeralRes=ephemeralRes
        options = [discord.SelectOption(label=x) for x in range(2,15)]
        super().__init__(placeholder='Select how many days from today', options=options, custom_id='selectDay')
    
    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        useEmojis = False
        if str(interaction.guild_id) in guildSettings and guildSettings[str(interaction.guild_id)]['useEmojis'] == 1:
            useEmojis = True
        
        value = self.values[0]
        msgArr = splitMsg(getDayList(ephemeris, value, useEmojis))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)

class SelectMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True):
        self.ephemeralRes=ephemeralRes
        options = [discord.SelectOption(label=x) for x in range(2,15)]
        super().__init__(placeholder='Select how many days from today', options=options)
    
    async def callback(self, interaction: discord.Interaction):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        value = self.values[0]
        msgArr = splitMsg(getDayList(ephemeris, value))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
        
class SelectViewPersist(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectMenuPersist())
        
class SelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectMenu())
        
class MenuNoPersist(discord.ui.View):
    def __init__(self, ephemeralRes=False, timeout=300):
        super().__init__(timeout=timeout)
        self.ephemeralRes=ephemeralRes
        self.add_item(SelectMenu(ephemeralRes))
                
    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red)
    async def yesterday(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        msgArr = splitMsg(getDayList(ephemeris, -1))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
        
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
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        msgArr = splitMsg(getDayList(ephemeris, 0))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    
    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple)
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            # Overridden as true so that users can use temporary menues made by users with permissions
            whiteListed = True
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        msgArr = splitMsg(getDayList(ephemeris, 1))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    

# Create seperate menu that wont persist
class GuildMenu(discord.ui.View):
    def __init__(self, ephemeralRes=True, timeout=None):
        super().__init__(timeout=timeout)
        self.ephemeralRes=ephemeralRes
        self.add_item(SelectMenuPersist(ephemeralRes))
                
    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red, custom_id='yesterday')
    async def yesterday(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        useEmojis = False
        if str(interaction.guild_id) in guildSettings and guildSettings[str(interaction.guild_id)]['useEmojis'] == 1:
            useEmojis = True
        msgArr = splitMsg(getDayList(ephemeris, -1, useEmojis))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
        
    @discord.ui.button(label="Today", style=discord.ButtonStyle.green, custom_id='today')
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        useEmojis = False
        if str(interaction.guild_id) in guildSettings and guildSettings[str(interaction.guild_id)]['useEmojis'] == 1:
            useEmojis = True
        
        msgArr = splitMsg(getDayList(ephemeris, 0, useEmojis))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    
    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple, custom_id='tomorrow')
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        whiteListed = False
        if 0 in interaction._integration_owners:
            whiteListed = str(interaction.guild_id) in guildWhiteList
        elif 1 in interaction._integration_owners:
            whiteListed = str(interaction.user.id) in userWhiteList
            
        if not whiteListed:
            await interaction.response.send_message(content='Server or user does not have permission to use this command', ephemeral=True)
            return
        
        useEmojis = False
        if str(interaction.guild_id) in guildSettings and guildSettings[str(interaction.guild_id)]['useEmojis'] == 1:
            useEmojis = True
        
        msgArr = splitMsg(getDayList(ephemeris, 1, useEmojis))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    
#######################
#  Helper Functions
#######################
def getDayList(ephemeris, day: int, useEmojis = False):
    currentTime = round((time.time()*1000))
    start = currentTime-round(0.25*oneDay ) if day == 0 else currentTime+int(day)*int(oneDay)
    end = currentTime+oneDay if day == 0 else start+oneDay
    cacheSubSet = ephemeris.getEventsInRange(start, end)
    startState = cacheSubSet[0]
    eventMsg = createEventMsgLine(startState, useEmojis, True)
    if len(cacheSubSet) > 1:
        for event in cacheSubSet[1:]:
            eventMsg += '\n' + createEventMsgLine(event, useEmojis)
    return eventMsg

def createEventMsgLine(event, useEmojis=True, firstEvent=False):
    glows = event['newGlows']
    darks = [i for i in event['newDarks'] if i != 'Shadow']
    normals = [i for i in event['returnedToNormal'] if i != 'Shadow']
    msg = f"> {event['discordTS']}"
    for index, cat in enumerate([glows, darks, normals]):
        tempMsg = ''
        if len(cat) < 1: continue
        elif len(cat) >= 3:
            if useEmojis:
                tempMsg += ' ' + ''.join([emojis[orb] for orb in cat]) + ' have '
            else:
                tempMsg += ' __' + '__, __'.join(cat[:-1]) + '__, and __' + cat[-1] + '__ have '
        elif len(cat) == 2:
            if useEmojis:
                tempMsg += ' ' + ''.join([emojis[orb] for orb in cat]) + ' have '
            else:
                tempMsg += ' __' +  cat[0] + "__ and __" + cat[1] + '__ have '
        elif len(cat) == 1: 
            if useEmojis:
                tempMsg += ' ' +  emojis[cat[0]] + ' has '
            else:
                tempMsg += ' __' +  cat[0] + '__ has '
            
        if index == 0: tempMsg += 'begun to **glow.**'
        elif index == 1: tempMsg += 'gone **dark.**'
        elif index == 2: tempMsg += 'returned to **normal.**'
        
        msg += tempMsg
    
    return msg
    
def splitMsg(msg):
    if len(msg) < 2001: return [msg]
    msgArr = []
    while len(msg) > 2000:
        # find last index in range
        i = msg[:2000].rfind('\n')
        msgArr.append(msg[:i-1])
        msg = msg[i:]
    return msgArr

def updateGuildSettings(settings, guildSettingsFile='src\\discordBot\\guildSettings.json'):
        json_object = json.dumps(settings, indent=4)
        with open(guildSettingsFile, "w") as outfile:
            outfile.write(json_object)
            
def getGuildSettings(guildSettingsFile='src\\discordBot\\guildSettings.json'):
    settings={}
    with open(guildSettingsFile, 'r') as json_file:
            settings = json.load(json_file)
    return settings