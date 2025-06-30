import discord
from discord.ext import commands, tasks
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

ANNOUNCE_CHANNEL_NAME = os.getenv("ANNOUNCEMENT_CHANNEL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_USERNAME = os.getenv("TWITCH_USERNAME")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class StreamNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_token = None
        self.last_youtube_video_id = None
        self.twitch_streaming = False
        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    async def get_twitch_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                data = await resp.json()
                return data.get("access_token")

    async def check_twitch(self):
        if not self.twitch_token:
            self.twitch_token = await self.get_twitch_token()

        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.twitch_token}"
        }
        url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                if data["data"]:
                    return data["data"][0]
                return None

    async def check_youtube(self):
        url = (
            f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}"
            f"&channelId={YOUTUBE_CHANNEL_ID}&part=snippet,id&order=date&maxResults=1"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if "items" in data:
                    return data["items"][0]
                return None

    @commands.command()
    async def testtwitch(self, ctx):
        """Force-check the Twitch stream status manually."""
        stream = await self.check_twitch()
        if stream:
            await ctx.send(f"🟢 F1NKST3R is LIVE!\n{stream['title']}")
        else:
            await ctx.send("🔴 Not live.")

    @tasks.loop(minutes=3)
    async def check_streams(self):
        await self.bot.wait_until_ready()
        channel = discord.utils.get(self.bot.get_all_channels(), name=ANNOUNCE_CHANNEL_NAME)
        if not channel:
            return

        # --- Twitch ---
        stream_data = await self.check_twitch()
        if stream_data and not self.twitch_streaming:
            self.twitch_streaming = True
            embed = discord.Embed(
                title="🔴 F1NKST3R is LIVE!",
                description="Try not to embarrass yourself in chat.",
                color=0x0da2ff
            )
            embed.add_field(name="📺 Watch Now", value=f"https://twitch.tv/{TWITCH_USERNAME}", inline=False)
            embed.set_footer(text="— F1NKTR0N")
            await channel.send(embed=embed)

        elif not stream_data:
            self.twitch_streaming = False

        # --- YouTube ---
        video = await self.check_youtube()
        if video:
            video_id = video["id"].get("videoId")
            if video_id != self.last_youtube_video_id:
                self.last_youtube_video_id = video_id
                title = video["snippet"]["title"]
                url = f"https://youtube.com/watch?v={video_id}"
                embed = discord.Embed(
                    title="📹 New Video!",
                    description=f"{title}",
                    color=0x0da2ff
                )
                embed.add_field(name="🎬 Watch it", value=url, inline=False)
                embed.set_footer(text="— F1NKTR0N")
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StreamNotify(bot))
