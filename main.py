from src import discordBot
import os
import time
from multiprocessing import Process
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 

def main():
    discordBot.bot.run(os.getenv("BOT_TOKEN"))
    
if __name__ == '__main__':
    ephemeris = discordBot.ephemeris
    refreshCacheProcess = Process(target=ephemeris.autoRefreshCache)
    refreshCacheProcess.start()
    main()