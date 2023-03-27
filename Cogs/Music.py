import asyncio, functools, itertools, math, random, discord, youtube_dl
from async_timeout import timeout
from discord.ext import commands
import os

def setup(bot):
    bot.add_cog(Music(bot))

youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog, name="음악"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

        self.embed_color = 0x75B8FF

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    lq = False

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)



    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        await ctx.message.add_reaction('✅')

    @commands.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        if not channel and not ctx.author.voice:
            raise VoiceError('음성 채널에 연결하지 않았습니다')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        await ctx.message.add_reaction('✅')

    @commands.command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('어느 채널에도 연결되어있지 않습니다')

        await ctx.voice_state.stop()
        await ctx.message.add_reaction('✅')
        del self.voice_states[ctx.guild.id]

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """현재 재생 중인 곡을 표시합니다."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    async def _pause(self, ctx: commands.Context):
        """현재 재생 중인 곡을 일시정지합니다."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
        """현재 일시정지 중인 곡을 재생합니다."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        ctx.voice_state.songs.clear()

        if not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('현재 음악이 재생중이지 않습니다.')

        await ctx.message.add_reaction('⏭')
        ctx.voice_state.skip()

    @commands.command(name='queue', aliases=["q"])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        if len(ctx.voice_state.songs) == 0:
            embed=(discord.Embed(title=":no_entry: **Error!**", description="대기열이 비었습니다.", color=self.embed_color)
                .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
            return await ctx.send(embed=embed)

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += f'`{i + 1}:` {song.source.title}\n'

        embed = (discord.Embed(title=":notepad_spiral: **대기열 목록**", description=f"**{page} 페이지 표시 중**", color=self.embed_color)
            .add_field(name=f'{len(ctx.voice_state.songs)} tracks:\n\n{queue}', value='page {}/{}'.format(page, pages), inline=True)
            .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
        await ctx.send(embed=embed)
    
    @commands.command(name='queuetest', aliases=["qt"])
    async def _qt(self, ctx: commands.Context):
        global queue
        queue = []

        embed = discord.Embed(title=":notepad_spiral: **대기열 목록**", description=".",).add_field(name=f'{len(ctx.voice_state.songs)} tracks:\n\n{queue}', value='..', inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='addsong', aliases=["as"])
    async def _addsong(self, ctx: commands.Context, search: str):
        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                embed=(discord.Embed(title=":no_entry: Error!", description=f"다음 요청을 처리하는 동안 오류가 발생했습니다: {str(e)}")
                    .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
                await ctx.send(embed=embed)
            else:
                song = Song(source)
                queue.append(ctx.voice_state.title)
                successful_embed=(discord.Embed(title=":white_check_mark: **대기열에 추가되었습니다**", description=f"{str(source)}", color=self.embed_color)
                    .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))

                await ctx.voice_state.songs.put(song)
                await ctx.send(embed=successful_embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        if len(ctx.voice_state.songs) == 0:
            embed=(discord.Embed(title=":no_entry: **Error!**", description="대기열이 비었습니다.", color=self.embed_color)
                .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
            return await ctx.send(embed=embed)

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove', aliases=["rm"])
    async def _remove(self, ctx: commands.Context, index: int):
        if len(ctx.voice_state.songs) == 0:
            embed=(discord.Embed(title=":no_entry: **Error!**", description="대기열이 비었습니다.", color=self.embed_color)
                .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
            return await ctx.send(embed=embed)

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('현재 재생중인 항목이 없습니다.')

        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='lq')
    async def _loop_queue(self, ctx:commands.Context):
        def find(filename, directory):
            if os.path.exists(directory+filename): # 파일이 존재한다면
                return True # True 반환
            else: # 아니면
                return False # False 반환

        def returnAddData(filename, directory, boolean):
            try: # 에러 처리
                f = open(directory+filename, "r") # 읽기 전용으로 파일 열기
                data = f.read() # 읽고 data에 저장
                f.close() # 파일 닫기
                f = open(directory+filename, "w") # 쓰기 전용으로 파일 열기
                f.write(str(data)+str(boolean)) # 더하기
                f.close() # 파일 닫기
            except FileNotFoundError: # 에러가 날 경우 
                print("Error : File not found") # 출력

        if not ctx.voice_state.is_playing:
            return await ctx.send('현재 재생중인 항목이 없습니다.')
        else:
            foundfile = find("lq.txt", "..\Cogs\options\\") # 파일이 있는지 확인
            if foundfile: # 존재하면
                f = open("..\Cogs\options\lq.txt", "r")
                data = f.read()
                f.close()
                f = open("..\Cogs\options\lq.txt", "w")
                f.close()
                if data == str(False):
                  returnAddData("lq.txt", "..\Cogs\options\\", True) # 파일에 추가
                  await ctx.send("Queue Loop Enabled!")
                  source = await YTDLSource.create_source(ctx, ctx.voice_state.title, loop=self.bot.loop)
                  song = Song(source)
                elif data == str(True):
                  returnAddData("lq.txt", "..\Cogs\options\\", False) # 파일에 추가
                  await ctx.send("Queue Loop disabled!")
                else:
                  returnAddData("lq.txt", "..\Cogs\options\\", True) # 파일에 추가
                  await ctx.send("Queue Loop enabled!")
                  source = await YTDLSource.create_source(ctx, ctx.voice_state.title, loop=self.bot.loop)
                  song = Song(source)
            else: # 못 찾으면
                f = open("..\Cogs\options\\lq.txt", "w+") # 파일 새로 생성
                f.write(str(True)) # 경고 쓰기
                f.close() # 파일 닫기                
                await ctx.send("Queue Loop Enabled!")
                source = await YTDLSource.create_source(ctx, ctx.voice_state.title, loop=self.bot.loop)
                song = Song(source)

    @commands.command(name='play', aliases=["p"])
    async def _play(self, ctx, *, search: str):
        global queue
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        def find(filename, directory):
            if os.path.exists(directory+filename): # 파일이 존재한다면
                return True # True 반환
            else: # 아니면
                return False # False 반환

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                embed=(discord.Embed(title=":no_entry: Error!", description=f"다음 요청을 처리하는 동안 오류가 발생했습니다: {str(e)}")
                    .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))
                await ctx.send(embed=embed)
            else:
                song = Song(source)
                queue.append(search)
                successful_embed=(discord.Embed(title=":white_check_mark: **대기열에 추가되었습니다**", description=f"{str(source)}", color=self.embed_color)
                    .set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url))

                foundfile = find("lq.txt", "..\Cogs\options\\") # 파일이 있는지 확인
                if foundfile: # 존재하면
                    f = open("..\Cogs\options\lq.txt", "r")
                    data = f.read()
                    f.close()
                    f = open("..\Cogs\options\lq.txt", "w")
                    f.close()
                    if data == str(True):
                        song = Song(source)

                    await ctx.voice_state.songs.put(song)
                    await ctx.send(embed=successful_embed)
                else:
                    f = open("..\Cogs\options\lq.txt", "w+") # 파일 새로 생성
                    f.write(str(False)) # 경고 쓰기
                    f.close() # 파일 닫기     

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel..')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Bot is already in a voice channel")