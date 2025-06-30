import discord
from discord.ext import commands

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[Onboarding] Cog loaded.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Try to find a general channel the bot can speak in
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    "🤖  **F1NKTR0N ONLINE**\n\n"
                    "Good evening, meat-sacks.  \n"
                    "I’ll be your automated disappointment manager from here on out.\n\n"
                    "**Live notifications?** I’ve got them.  \n"
                    "**New video drops?** Already queued.  \n"
                    "**Tech support?** Try turning your brain off and on again.\n\n"
                    "*Carry on… and don’t trip over the power cord.*"
                )
                break

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
