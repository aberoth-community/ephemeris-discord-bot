from .discordBot import bot, ephemeris
from .Ephemeris import Ephemeris
import os
import time
from multiprocessing import Process
from dotenv import load_dotenv

load_dotenv()


def main():
    bot.run(os.getenv("BOT_TOKEN"))


if __name__ == "__main__":
    # For intermitantly refreshing cache and recalibrating
    # refreshCacheProcess = Process(target=ephemeris.autoRefreshCache)
    # refreshCacheProcess.start()
    main()
