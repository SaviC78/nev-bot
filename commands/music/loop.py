import discord
from discord.ext import commands
import wavelink

class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="loop")
    async def loop(self, ctx):
        """Toggle queue loop"""
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

        if not vc.queue:
            error_embed.description = "There's nothing in the queue to loop!"
            return await ctx.send(embed=error_embed)

        vc.queue.loop = not vc.queue.loop
        await ctx.send(f"🔁 Loop {'enabled' if vc.queue.loop else 'disabled'}!")

async def setup(bot):
    await bot.add_cog(Loop(bot)) 