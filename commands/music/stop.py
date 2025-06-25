import discord
from discord.ext import commands
import wavelink

class Stop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop playing and clear the queue"""
        # Create error embed
        error_embed = discord.Embed(
            title="Error",
            description=""
        )

        if not ctx.voice_client:
            error_embed.description = "I'm not connected to a voice channel!"
            return await ctx.send(embed=error_embed)

        if not ctx.author.voice:
            error_embed.description = "You must be in a voice channel to use this command!"
            return await ctx.send(embed=error_embed)

        vc: wavelink.Player = ctx.voice_client

        if not vc.playing:
            error_embed.description = "Nothing is currently playing!"
            return await ctx.send(embed=error_embed)

        await vc.stop()
        vc.queue.clear()
        await ctx.send("⏹️ Stopped!")

async def setup(bot):
    await bot.add_cog(Stop(bot)) 