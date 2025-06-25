import discord
from discord.ext import commands
import wavelink

class Remove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="remove")
    async def remove(self, ctx, position: int):
        """Remove a track from the queue"""
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
            error_embed.description = "The queue is empty!"
            return await ctx.send(embed=error_embed)

        if position < 1 or position > len(vc.queue):
            error_embed.description = f"Please provide a valid position between 1 and {len(vc.queue)}!"
            return await ctx.send(embed=error_embed)

        track = vc.queue[position - 1]
        vc.queue.remove(track)
        await ctx.send(f"🗑️ Removed **{track.title}** from the queue!")

async def setup(bot):
    await bot.add_cog(Remove(bot)) 