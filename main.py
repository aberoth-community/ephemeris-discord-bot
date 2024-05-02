from src import discordBot
import os
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 

discordBot.bot.run(os.getenv("BOT_TOKEN"))