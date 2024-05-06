from .discordBot import bot, ephemeris
import os
from multiprocessing import Process
from dotenv import load_dotenv

load_dotenv()


def main():
    bot.run(os.getenv("BOT_TOKEN"))


if __name__ == "__main__":
    refreshCacheProcess = Process(target=ephemeris.autoRefreshCache)
    refreshCacheProcess.start()
    main()
