import discord
from discord.ext import commands
import wavelink

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx, volume: int = None):
        """Change the volume (0-100)"""
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

        if volume is None:
            return await ctx.send(f"🔊 Current volume: {vc.volume}%")

        if not 0 <= volume <= 100:
            error_embed.description = "Volume must be between 0 and 100!"
            return await ctx.send(embed=error_embed)

        await vc.set_volume(volume)
        await ctx.send(f"🔊 Volume set to {volume}%")

async def setup(bot):
    await bot.add_cog(Volume(bot)) 