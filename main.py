from replit import db
import asyncio
import discord
from discord.ext import commands
import random
from discord.utils import get
import os
import requests
import json
from keep_alive import keep_alive

app = commands.Bot(command_prefix='?')
client = discord.Client()

for filename in os.listdir("Cogs"):
    if filename.endswith(".py"):
        app.load_extension(f"Cogs.{filename[:-3]}")


def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    return (quote)


@app.event
async def on_ready():
    print("Bot Online")
    game = discord.Game("매우 아주 극심하고 격렬하게 집가고싶다")
    await app.change_presence(status=discord.Status.online, activity=game)


@app.command()
async def ping(ctx):
    la = app.latency
    embed = discord.Embed(title=":ping_pong:   pong!",
                          description=f"**{(round(la * 1000))}** ms",
                          color=0x00ffd8)
    await ctx.send(embed=embed)


@app.command(name="load")
async def load_commands(ctx, extension):
    app.load_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 로드했습니다!")


@app.command(name="unload")
async def unload_commands(ctx, extension):
    app.unload_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 언로드했습니다!")


@app.command(name="reload")
async def reload_commands(ctx, extension=None):
    if extension is None:  # extension이 None이면 (그냥 !리로드 라고 썼을 때)
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py"):
                app.unload_extension(f"Cogs.{filename[:-3]}")
                app.load_extension(f"Cogs.{filename[:-3]}")
                await ctx.send(":white_check_mark: 모든 명령어를 다시 불러왔습니다!")
    else:
        app.unload_extension(f"Cogs.{extension}")
        app.load_extension(f"Cogs.{extension}")
        await ctx.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다!")


@app.command(name="비판")
async def send_dm(ctx):
    await ctx.send(
        "Korean\n`비판을 용납할 수 없다면, 비판을 하지도 말지어다.`\n\nEnglish\n`If you can't handle criticism, don't criticize.`\n\nDutch\n`Wie boter op zijn hoofd heeft, moet uit de zon blijven.`"
    )


@app.command(name="솔린디", aliases=['솔방울'])
async def solindy(ctx):
    await ctx.send('개천재 ㄹㅇ')


@app.command(name="토리", aliases=['도토리', '도토리묵'])
async def tori(ctx):
    await ctx.send('개빡대가리 ㄹㅇ')


@app.command(name="파인드",
             aliases=['ㅍㅇㄷ', '파인드애플', 'pined', 'pinedapple', 'pined_apple'])
async def pined(ctx):
    await ctx.send('가끔씩은 개천재')

@app.command(name="sex")
async def sex(ctx):
    await ctx.send('하읏..')

app.remove_command("help")

keep_alive()
app.run(os.getenv('TOKEN'))
