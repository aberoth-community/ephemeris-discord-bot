
from typing import Any, Coroutine
import discord
from discord import app_commands
from discord.ext import commands
from .helperFuncs import *

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

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
    
@bot.tree.command(name='say')
@app_commands.describe(thing_to_say = 'What should I say?')
async def say(interaction: discord.Interaction, thing_to_say: str):
    await interaction.response.send_message(f"{interaction.user.name} said: {thing_to_say}")

@bot.tree.command(name='create_prediction_menu')
async def menu(interaction: discord.Interaction):
    embed = discord.Embed(title='**Select What day you would like the scroll events for.**',
                          description='*Glows should be accurate within a handful of seconds*',
                          color=0xA21613)
    embed.add_field(name="**__Details:__**",
                    value=
                    "**``Yesterday:``** Returns all scroll events between now and 24 hours ago.\n"
                    "\n**``Today:    ``** Returns all scroll events between 6 hours ago and 24 hours from now.\n"
                    "\n**``Tomorrow: ``** Returns all scroll events between 24 hours from now to 48 hours from now.",
                    inline=False
    )
    embed.set_thumbnail(url='https://i.imgur.com/CkCJDlT.png')
    await interaction.response.send_message(embed=embed, view = Menu(), ephemeral=True)

####################
#      Menus
#################### 
class SelectMenu(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=x) for x in range(2,14)]
        super().__init__(placeholder='Select how many days from today', options=options)
    
    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        await interaction.response.send_message(content=getDayList(value), ephemeral=True)
        
        
class SelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectMenu())
        
class Menu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectMenu())
        #self.add_item(discord.ui.Button(label='test'))
        
    @discord.ui.button(label="Yesterday", style=discord.ButtonStyle.red)
    async def yesterday(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"{getDayList(-1)}", ephemeral=True)
        
    @discord.ui.button(label="Today", style=discord.ButtonStyle.green)
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f"{getDayList(0)}", ephemeral=True)
    
    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.blurple)
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=getDayList(1), ephemeral=True)
    
    #row1 = discord.ActionRow(components=[yesterday,today])
    