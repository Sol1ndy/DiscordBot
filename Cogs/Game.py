import discord
from discord.ext import commands
import random
from discord.utils import get
import os
import pickle

class Game(commands.Cog, name="게임"):
    """
    게임 명령어들입니다. 아직 개발되지 않았습니다.
    """

    def __init__(self, app):
        self.app = app

def setup(app):
    app.add_cog(Game(app))
