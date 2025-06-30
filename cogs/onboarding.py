import discord
from discord.ext import commands

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[Onboarding] Cog loaded.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        message = (
            "🤖  **F1NKTR0N ONLINE**\n\n"
            "Good evening, meat-sacks.  \n"
            "I’ll be your automated disappointment manager from here on out.\n\n"
            "**Live notifications?** I’ve got them.  \n"
            "**New video drops?** Already queued.  \n"
            "**Tech support?** Try turning your brain off and on again.\n\n"
            "*Carry on… and don’t trip over the power cord.*"
        )

        # Define priority names
        preferred_names = ["general", "chat"]
        excluded_keywords = ["rules", "announce", "announcement"]

        # Try to find a preferred channel first
        for name in preferred_names:
            for channel in guild.text_channels:
                if name in channel.name.lower() and channel.permissions_for(guild.me).send_messages:
                    if not any(exclude in channel.name.lower() for exclude in excluded_keywords):
                        await channel.send(message)
                        return

        # Fallback: post in first allowed channel that isn't excluded
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if not any(exclude in channel.name.lower() for exclude in excluded_keywords):
                    await channel.send(message)
                    return

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
