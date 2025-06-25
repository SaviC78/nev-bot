import discord
from discord.ext import commands
import wavelink
import random

class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Shuffle the current queue"""
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

        if len(vc.queue) < 2:
            error_embed.description = "Need at least 2 songs in the queue to shuffle!"
            return await ctx.send(embed=error_embed)

        # Convert queue to list, shuffle, and put back
        queue_list = list(vc.queue)
        random.shuffle(queue_list)
        vc.queue.clear()
        for track in queue_list:
            await vc.queue.put_wait(track)

        await ctx.send("🔀 Queue shuffled!")

async def setup(bot):
    await bot.add_cog(Shuffle(bot)) 