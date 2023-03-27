import random
import discord
from discord.ext import commands
from discord.utils import get
import pickle
import asyncio

class Event(commands.Cog, name="이벤트"):
    """
    이벤트때 사용 가능한 명령어들입니다.
    """

    def __init__(self, app):
        self.app = app
        
    @commands.command(name="옵치대회", help="VGS 오버워치 대회 명령어")
    @commands.has_permissions(administrator=True)
    async def Overwatch(self, ctx):
        tt = 1
        if tt == 1:
            team1 = ['김성진', '김민찬', '이윤재', '지하람', '유우민', '나영민']
            team2 = ['김강현', '김동희', '안유근', '김호중', '권영우', '김태진']
            heroes1 = ['아나', '애쉬', '바티스트', '바스티온', '브리기테', '디바', '둠피스트', '에코', '겐지', '한조', '정크랫', '루시우',
                       '캐서디', '메이', '메르시', '모이라', '오리사', '파라', '리퍼', '라인하르트', '로드호그', '시그마', '솔저:76', '솜브라',
                       '시메트라', '토르비욘', '트레이서', '위도우메이커', '윈스턴', '레킹볼', '자리야', '젠야타']
            heroes2 = ['아나', '애쉬', '바티스트', '바스티온', '브리기테', '디바', '둠피스트', '에코', '겐지', '한조', '정크랫', '루시우',
                       '캐서디', '메이', '메르시', '모이라', '오리사', '파라', '리퍼', '라인하르트', '로드호그', '시그마', '솔저:76', '솜브라',
                       '시메트라', '토르비욘', '트레이서', '위도우메이커', '윈스턴', '레킹볼', '자리야', '젠야타']
            t1p1 = random.choice(team1)
            team1.remove(t1p1)
            t1p2 = random.choice(team1)
            team1.remove(t1p2)
            t1p3 = random.choice(team1)
            team1.remove(t1p3)
            t1p4 = random.choice(team1)
            team1.remove(t1p4)
            t1p5 = random.choice(team1)
            team1.remove(t1p5)
            t1p6 = random.choice(team1)
            team1.remove(t1p6)

            t1h1 = random.choice(heroes1)
            heroes1.remove(t1h1)
            t1h2 = random.choice(heroes1)
            heroes1.remove(t1h2)
            t1h3 = random.choice(heroes1)
            heroes1.remove(t1h3)
            t1h4 = random.choice(heroes1)
            heroes1.remove(t1h4)
            t1h5 = random.choice(heroes1)
            heroes1.remove(t1h5)
            t1h6 = random.choice(heroes1)
            heroes1.remove(t1h6)

            t2p1 = random.choice(team2)
            team2.remove(t2p1)
            t2p2 = random.choice(team2)
            team2.remove(t2p2)
            t2p3 = random.choice(team2)
            team2.remove(t2p3)
            t2p4 = random.choice(team2)
            team2.remove(t2p4)
            t2p5 = random.choice(team2)
            team2.remove(t2p5)
            t2p6 = random.choice(team2)
            team2.remove(t2p6)

            t2h1 = random.choice(heroes2)
            heroes2.remove(t2h1)
            t2h2 = random.choice(heroes2)
            heroes2.remove(t2h2)
            t2h3 = random.choice(heroes2)
            heroes2.remove(t2h3)
            t2h4 = random.choice(heroes2)
            heroes2.remove(t2h4)
            t2h5 = random.choice(heroes2)
            heroes2.remove(t2h5)
            t2h6 = random.choice(heroes2)
            heroes2.remove(t2h6)

            await ctx.send("```오버워치 대회 2세트 랜덤픽 편성이 완료되었습니다.```")
            await asyncio.sleep(1)
            await ctx.send("----------1팀----------")
            await asyncio.sleep(0.1)
            await ctx.send(f"{t1p1}  ----> {t1h1} \n{t1p2}  ----> {t1h2} \n{t1p3}  ----> {t1h3} \n{t1p4}  ----> {t1h4} \n{t1p5}  ----> {t1h5} \n{t1p6}  ----> {t1h6}")
            await asyncio.sleep(0.5)
            await ctx.send(f"\n----------2팀----------")
            await asyncio.sleep(0.1)
            await ctx.send(f"{t2p1}  ----> {t2h1} \n{t2p2}  ----> {t2h2} \n{t2p3}  ----> {t2h3} \n{t2p4}  ----> {t2h4} \n{t2p5}  ----> {t2h5} \n{t2p6}  ----> {t2h6} \n")

def setup(app):
    app.add_cog(Event(app))