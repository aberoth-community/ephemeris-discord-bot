import time
import copy
from typing import Optional
import discord.types
from regex import match
from discord import app_commands
from discord.ext import commands
from ..Ephemeris import Ephemeris
from .configFiles.variables import *

ephemeris = Ephemeris.Ephemeris(
    start=(time.time() * 1000) + cacheStartDay * oneDay, 
    end=(time.time() * 1000) + cacheEndDay * oneDay,
    numMoonCycles=numMoonCycles
)