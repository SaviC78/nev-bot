import discord
from discord.ext import commands
import wavelink

class Pause(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the current song"""
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

        # Check if the player is already paused
        if vc.paused:
            error_embed.description = "The player is already paused!"
            return await ctx.send(embed=error_embed)

        try:
            # Send response first
            success_embed = discord.Embed(description="⏸️ Paused!")
            await ctx.send(embed=success_embed)
            
            # Pause the player
            await vc.pause(True)

            # Update the now playing message's pause button if it exists
            music_cog = self.bot.get_cog("Play")
            if music_cog and ctx.guild.id in music_cog.now_playing_messages:
                message = music_cog.now_playing_messages[ctx.guild.id]
                # Create a new view with updated buttons
                view = discord.ui.View()
                
                # Add all buttons with updated pause button
                for child in message.components[0].children:
                    if child.custom_id in ["pause", "resume"]:
                        # Create new resume button
                        new_button = discord.ui.Button(
                            emoji="▶️",
                            style=discord.ButtonStyle.grey,
                            custom_id="resume"
                        )
                        # Get the callback from the existing button
                        new_button.callback = child.callback
                        view.add_item(new_button)
                    else:
                        # Copy other buttons as is
                        new_button = discord.ui.Button(
                            emoji=child.emoji,
                            style=child.style,
                            custom_id=child.custom_id
                        )
                        # Get the callback from the existing button
                        new_button.callback = child.callback
                        view.add_item(new_button)
                
                await message.edit(view=view)

        except Exception as e:
            error_embed.description = f"An error occurred: {str(e)}"
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Pause(bot)) 