import time
import copy
from typing import Optional
import discord.types
from regex import match
from discord import app_commands
from discord.ext import commands
from ..Ephemeris import Ephemeris
from .configFiles.variables import *
from .configFiles.dataBase import *

ephemeris = Ephemeris.Ephemeris(
    start=(time.time() * 1000) + -4 * oneDay,
    end=(time.time() * 1000) + 35 * oneDay,
    numMoonCycles=numMoonCycles,
    discordTimestamps=True,
    multiProcess=True,
)
