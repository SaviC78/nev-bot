import discord
from discord.ext import commands
import wavelink

class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the current song"""
        # Create error embed
        error_embed = discord.Embed(
            title="Error",
            description=""
        )

        # Check if bot is in a voice channel
        if not ctx.voice_client:
            error_embed.description = "I'm not connected to a voice channel!"
            return await ctx.send(embed=error_embed)

        # Check if user is in a voice channel
        if not ctx.author.voice:
            error_embed.description = "You must be in a voice channel to use this command!"
            return await ctx.send(embed=error_embed)

        # Check if user is in the same voice channel as the bot
        if ctx.author.voice.channel != ctx.voice_client.channel:
            error_embed.description = "You must be in the same voice channel as me!"
            return await ctx.send(embed=error_embed)

        vc: wavelink.Player = ctx.voice_client

        # Check if something is playing
        if not vc.playing:
            error_embed.description = "Nothing is currently playing!"
            return await ctx.send(embed=error_embed)

        try:
            # Create success embed first
            success_embed = discord.Embed(
                description="⏭️ Skipped!"
            )
            await ctx.send(embed=success_embed)

            # Get the next track before stopping the current one
            next_track = None
            if not vc.queue.is_empty:
                next_track = await vc.queue.get_wait()
            
            # Stop current track
            await vc.stop()
            
            # If there's a next track, play it
            if next_track:
                await vc.play(next_track)
                # Get the Play cog instance to create the now playing embed
                music_cog = self.bot.get_cog("Play")
                if music_cog:
                    # Delete old now playing message if it exists
                    if ctx.guild.id in music_cog.now_playing_messages:
                        try:
                            await music_cog.now_playing_messages[ctx.guild.id].delete()
                        except:
                            pass
                    # Create new now playing embed
                    await music_cog.create_now_playing_embed(ctx, next_track)
        except Exception as e:
            error_embed.description = f"An error occurred: {str(e)}"
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Skip(bot)) 