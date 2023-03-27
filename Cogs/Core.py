import discord
from discord.ext import commands
import random
from discord.utils import get
import os
import pickle

class Admin(commands.Cog, name="관리자"):
    """
    관리자들만 사용할 수 있는 명령어입니다
    """

    def __init__(self, app):
        self.app = app

    @commands.command(help="정한 숫자만큼 메시지를 삭제합니다.", usage="`!clean <숫자>`")
    async def clean(self, ctx, amount):
        if ctx.message.author.guild_permissions.change_nickname:
            try:
                if str(amount) >= str(51):
                    await ctx.send("50 이하의 수를 입력해 주세요.")
                else:
                    await ctx.message.channel.purge(limit=int(amount) + 1)
                    await ctx.send(f"**{amount}**개의 메시지를 지웠습니다.")
            except ValueError:
                await ctx.send("청소하실 메시지의 **수**를 입력해 주세요.")
        else:
            await ctx.send("당신은 권한이 없기 때문에 이 명령어를 사용할 수 없습니다")

def setup(app):
    app.add_cog(Admin(app))
