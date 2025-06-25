import discord
from discord.ext import commands
import wavelink

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear")
    async def clear(self, ctx):
        """Clear the current queue"""
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

        if not ctx.voice_client.queue:
            error_embed.description = "The queue is already empty!"
            return await ctx.send(embed=error_embed)

        ctx.voice_client.queue.clear()
        await ctx.send("🗑️ Queue cleared!")

async def setup(bot):
    await bot.add_cog(Clear(bot)) 