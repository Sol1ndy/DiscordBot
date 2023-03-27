import discord
from discord.ext import commands
import random
from discord.utils import get
import pickle
import re

class Common(commands.Cog, name="기본"):
    """
    솔린디 봇의 기본 명령어들입니다
    """

    def __init__(self, app):
        self.app = app
    
    @commands.command(help="설정한 숫자의 범위 안에서 랜덤한 숫자를 하나 뽑습니다", usage="`!randomnumber/rn <숫자 1> <숫자 2>`")
    async def rn(self, ctx, num1, num2):
        try:
            picked = random.randint(int(num1), int(num2))
            await ctx.send(f'뽑힌 숫자는 **{str(picked)}** 입니다')
        except IndexError:
            await ctx.send("무슨 숫자를 뽑을지 알려주세요")
        except ValueError:
            await ctx.channel.send("정수를 입력해주세요")
        except ZeroDivisionError:
            await ctx.channel.send("0으로 나눌 수 없습니다")

    @commands.command(name="도움말", help="도움말을 출력합니다.")
    async def help_command(self, ctx, func=None):
        cog_list = ["기본","관리자", "음악"]
        if func is None:
            embed = discord.Embed(title="VGS Bot 도움말", description="접두사는 `?` 입니다.", color=0x00ffd8)  # Embed 생성
            for x in cog_list:  # cog_list에 대한 반복문
                cog_data = self.app.get_cog(x)  # x에 대해 Cog 데이터를 구하기
                command_list = cog_data.get_commands()  # cog_data에서 명령어 리스트 구하기
                embed.add_field(name=x, value=" ".join([c.name for c in command_list]), inline=True)  # 필드 추가
            await ctx.send(embed=embed)  # 보내기
        else:
            command_notfound = True  # 이걸 어떻게 쓸지 생각해보세요!
            for _title, cog in self.app.cogs.items():  # title, cog로 item을 돌려주는데 title은 필요가 없습니다.
                if not command_notfound:  # False면
                    break  # 반복문 나가기
                else:  # 아니면
                    for title in cog.get_commands():  # 명령어를 아까처럼 구하고 title에 순차적으로 넣습니다.
                        if title.name == func:  # title.name이 func와 같으면
                            cmd = self.app.get_command(title.name)  # title의 명령어 데이터를 구합니다.
                            embed = discord.Embed(title=f"명령어 : {cmd}", description=cmd.help, color=0x00ffd8)  # Embed 만들기
                            await ctx.send(embed=embed)  # 보내기
                            command_notfound = False
                            break  # 반복문 나가기
                        else:
                            command_notfound = True
            if command_notfound:  # 명령어를 찾지 못하면
                if func in cog_list:  # 만약 cog_list에 func가 존재한다면
                    cog_data = self.get_cog(func)  # cog 데이터 구하기
                    command_list = cog_data.get_commands()  # 명령어 리스트 구하기
                    embed = discord.Embed(title=f"카테고리 : {cog_data.qualified_name}",
                                          description=cog_data.description, color=0x00ffd8)  # 카테고리 이름과 설명 추가
                    embed.add_field(name="명령어들",
                                    value=", ".join([c.name for c in command_list]))  # 명령어 리스트 join
                    await ctx.send(embed=embed)  # 보내기
                else:
                    await ctx.send("그런 이름의 명령어나 카테고리는 없습니다.")  # 에러 메시지
                    

def setup(app):
    app.add_cog(Common(app))
