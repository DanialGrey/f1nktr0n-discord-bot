import discord
from discord.ext import commands, tasks
import os
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Environment variables
ANNOUNCE_CHANNEL_NAME = os.getenv("ANNOUNCEMENT_CHANNEL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_USERNAME = os.getenv("TWITCH_USERNAME")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# YouTube ID cache path
KNOWN_IDS_FILE = Path("data/known_youtube_ids.json")

class StreamNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_token = None
        self.twitch_streaming = False
        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    def load_known_ids(self):
        if KNOWN_IDS_FILE.exists():
            with open(KNOWN_IDS_FILE, "r") as f:
                return set(json.load(f).get("known_video_ids", []))
        return set()

    def save_known_ids(self, known_ids):
        KNOWN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(KNOWN_IDS_FILE, "w") as f:
            json.dump({"known_video_ids": list(known_ids)}, f, indent=2)

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
        uploads_playlist = f"UU{YOUTUBE_CHANNEL_ID[2:]}"
        url = (
            f"https://www.googleapis.com/youtube/v3/playlistItems"
            f"?part=snippet&playlistId={uploads_playlist}&maxResults=1&key={YOUTUBE_API_KEY}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if "items" in data and data["items"]:
                    return data["items"][0]
                return None

    @tasks.loop(minutes=3)
    async def check_streams(self):
        await self.bot.wait_until_ready()
        channel = discord.utils.get(self.bot.get_all_channels(), name=ANNOUNCE_CHANNEL_NAME)
        if not channel:
            return

        # --- Twitch Check ---
        stream_data = await self.check_twitch()
        if stream_data and not self.twitch_streaming:
            self.twitch_streaming = True
            embed = discord.Embed(
                title=f"🔴 {stream_data['title']}",
                description="F1NKST3R just went live. Try not to disappoint him.",
                color=0x0da2ff
            )
            embed.add_field(name="📺 Watch Now", value=f"https://twitch.tv/{TWITCH_USERNAME}", inline=False)
            embed.set_footer(text="— F1NKTR0N")
            await channel.send(embed=embed)

        elif not stream_data:
            self.twitch_streaming = False

        # --- YouTube Check ---
        known_ids = self.load_known_ids()
        video = await self.check_youtube()
        if video:
            video_id = video["snippet"]["resourceId"]["videoId"]
            if video_id not in known_ids:
                title = video["snippet"]["title"]
                thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                url = f"https://youtube.com/watch?v={video_id}"

                embed = discord.Embed(
                    title="📹 New Video!",
                    description=title,
                    color=0x0da2ff
                )
                embed.set_image(url=thumbnail)
                embed.add_field(name="🎬 Watch it now", value=url, inline=False)
                embed.set_footer(text="— F1NKTR0N")

                await channel.send(embed=embed)
                known_ids.add(video_id)
                self.save_known_ids(known_ids)

async def setup(bot):
    await bot.add_cog(StreamNotify(bot))
