import time
import json
import discord
from discord import app_commands
from discord.ext import commands
from src.ephemeris import Ephemeris

f = open('src\\discordBot\\guildWhiteList.json')
whiteList = json.load(f)
oneDay = 86400000
ephemeris = Ephemeris.Ephemeris(start=(time.time()*1000)-2*86400000, end=(time.time()*1000)+16*86400000)

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix='', intents=intents)
    async def setup_hook(self) -> None:
        self.add_view(Menu())
        
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
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!", ephemeral=True)

@bot.tree.command(name="apptest", description="...")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def apptest(interaction: discord.Interaction):
    await interaction.response.send_message("I can be used anywhere, and am installed to guilds and users.")

@bot.tree.command(name='create_prediction_menu')
async def menu(interaction: discord.Interaction):
    ephRes = True
    fromGuild = False if interaction.guild is None else True
    # check if the menu is a guild menu or user install
    userInstall = False
    if userInstall: ephRes = False
    if str(interaction.guild_id) not in whiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
    embed = discord.Embed(title='**Select What day you would like the scroll events for.**',
                          description='*Glows should be accurate within a handful of seconds*',
                          color=0xA21613)
    embed.add_field(name="**__Details:__**",
                    value=
                    "​\n**``Yesterday:``** Returns all scroll events between now and 24 hours ago."
                    "\n\n**``Today:    ``** Returns all scroll events between 6 hours ago and 24 hours from now."
                    "\n\n**``Tomorrow: ``** Returns all scroll events between 24 hours from now to 48 hours from now."
                    "\n\n**``Later:    ``** Use the drop down menu to select what day from now you'd like the scroll events for",
                    inline=False
    )
    embed.set_thumbnail(url='https://i.imgur.com/CkCJDlT.png')
    await interaction.response.send_message(embed=embed, view = Menu(ephemeralRes=ephRes, fromGuild=fromGuild), ephemeral=False)

####################
#      Menus
#################### 
class SelectMenu(discord.ui.Select):
    def __init__(self, ephemeralRes=True):
        self.ephemeralRes =ephemeralRes
        options = [discord.SelectOption(label=x) for x in range(2,15)]
        super().__init__(placeholder='Select how many days from today', options=options, custom_id='selectDay')
    
    async def callback(self, interaction: discord.Interaction):
        if str(interaction.guild_id) not in whiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
        value = self.values[0]
        msgArr = splitMsg(getDayList(ephemeris, value))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
        
        
class SelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectMenu())
        
class Menu(discord.ui.View):
    def __init__(self, ephemeralRes=True, fromGuild=True):
        #self.TO = None if fromGuild else 180
        super().__init__(timeout=None)
        self.ephemeralRes=ephemeralRes
        self.add_item(SelectMenu(ephemeralRes))
                
    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red, custom_id='yesterday')
    async def yesterday(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.guild_id) not in whiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
        print("interaction:", interaction._integration_owners)
        msgArr = splitMsg(getDayList(ephemeris, -1))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
        
    @discord.ui.button(label="Today", style=discord.ButtonStyle.green, custom_id='today')
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.guild_id) not in whiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
        msgArr = splitMsg(getDayList(ephemeris, 0))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    
    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple, custom_id='tomorrow')
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.guild_id) not in whiteList:
            await interaction.response.send_message(content='Server does not have permission to use this command', ephemeral=True)
            return
        msgArr = splitMsg(getDayList(ephemeris, 1))
        await interaction.response.send_message(content=msgArr[0], ephemeral=self.ephemeralRes)
        if len(msgArr) > 1:
            for msg in msgArr:
                await interaction.followup.send(content=msg, ephemeral=self.ephemeralRes)
    
    #row1 = discord.ActionRow(components=[yesterday,today])
   
#######################
#  Helper Functions
#######################
def getDayList(ephemeris, day: int):
    currentTime = round((time.time()*1000))
    start = currentTime-round(0.25*oneDay )if day == 0 else currentTime+int(day)*int(oneDay)
    end = currentTime+oneDay if day == 0 else start+oneDay
    cacheSubSet = ephemeris.getEventsInRange(start, end)
    startState = cacheSubSet[0]
    eventMsg = createEventMsgLine(startState, True)
    if len(cacheSubSet) > 1:
        for event in cacheSubSet[1:]:
            eventMsg += '\n' + createEventMsgLine(event)
    return eventMsg

def createEventMsgLine(event, firstEvent=False):
    glows = event['newGlows']
    darks = [i for i in event['newDarks'] if i != 'Shadow']
    normals = [i for i in event['returnedToNormal'] if i != 'Shadow']
    msg = f"> {event['discordTS']}"
    for index, cat in enumerate([glows, darks, normals]):
        tempMsg = ''
        if len(cat) < 1: continue
        elif len(cat) >= 3:
            tempMsg += ' ' + ', '.join(cat[:-1]) + ', and ' + cat[-1] + ' have '
        elif len(cat) == 2:
            tempMsg += ' ' +  cat[0] + " and " + cat[1] + ' have '
        elif len(cat) == 1: 
            tempMsg += ' ' +  cat[0] + ' has '
            
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