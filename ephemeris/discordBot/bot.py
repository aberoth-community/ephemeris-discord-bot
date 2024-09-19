from .guildScrollMenus import *
from .guildLunarMenus import *


# allows for menus to persist and continue working between bot restarts
class PersistentViewBot(commands.Bot):
    def __init__(self): 
        intents = discord.Intents().all()
        super().__init__(command_prefix="~", intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(GuildScrollMenu(allow_filters=1, setUp=False))
        self.add_view(GuildLunarMenu())


bot = PersistentViewBot()

@bot.event
async def on_ready():
    print("Bot is up and ready!")
    try:
        synched = await bot.tree.sync()
        print(f"synched {len(synched)} command(s)")
    except Exception as e:
        print(e)