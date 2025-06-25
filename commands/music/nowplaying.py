import discord
from discord.ext import commands
import wavelink

class NowPlaying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.now_playing_messages = {}  # Store now playing messages per guild

    async def create_now_playing_embed(self, ctx, track):
        """Create and send the now playing embed with controls"""
        # Create now playing embed
        embed = discord.Embed(
            title="Now Playing",
            description=f"**{track.title}**"
        )
        
        # Add author with bot's avatar
        embed.set_author(
            name=ctx.guild.me.display_name,
            icon_url=ctx.guild.me.display_avatar.url
        )
        
        # Add track details
        if hasattr(track, 'author'):
            embed.add_field(
                name="Artist",
                value=track.author,
                inline=True
            )
        
        # Add duration if available
        if hasattr(track, 'duration'):
            duration = str(track.duration).split('.')[0]  # Remove milliseconds
            embed.add_field(
                name="Duration",
                value=duration,
                inline=True
            )
        
        # Add source if available
        if hasattr(track, 'source'):
            embed.add_field(
                name="Source",
                value=track.source.title(),
                inline=True
            )
        
        # Add thumbnail (cover image) if available
        if hasattr(track, 'artwork'):
            embed.set_thumbnail(url=track.artwork)

        # Create buttons
        class MusicControls(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.pause_button = discord.ui.Button(emoji="⏸️", style=discord.ButtonStyle.grey, custom_id="pause")
                self.pause_button.callback = self.pause_callback
                self.add_item(self.pause_button)

                self.skip_button = discord.ui.Button(emoji="⏭️", style=discord.ButtonStyle.grey, custom_id="skip")
                self.skip_button.callback = self.skip_callback
                self.add_item(self.skip_button)

                self.loop_button = discord.ui.Button(emoji="🔁", style=discord.ButtonStyle.grey, custom_id="loop")
                self.loop_button.callback = self.loop_callback
                self.add_item(self.loop_button)

            async def pause_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    await interaction.followup.send("You must be in a voice channel to use this!", ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    await interaction.followup.send("You must be in the same voice channel as the bot!", ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    await interaction.followup.send("Nothing is currently playing!", ephemeral=True)
                    return

                try:
                    if vc.paused:
                        await vc.pause(False)  # Resume
                        self.pause_button.emoji = "⏸️"
                        self.pause_button.custom_id = "pause"
                        await interaction.message.edit(view=self)
                        await interaction.followup.send("▶️ Resumed!", ephemeral=True)
                    else:
                        await vc.pause(True)  # Pause
                        self.pause_button.emoji = "▶️"
                        self.pause_button.custom_id = "resume"
                        await interaction.message.edit(view=self)
                        await interaction.followup.send("⏸️ Paused!", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"Failed to toggle pause state: {str(e)}", ephemeral=True)

            async def skip_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    await interaction.followup.send("You must be in a voice channel to use this!", ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    await interaction.followup.send("You must be in the same voice channel as the bot!", ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    await interaction.followup.send("Nothing is currently playing!", ephemeral=True)
                    return

                try:
                    await vc.stop()
                    await interaction.followup.send("⏭️ Skipped!", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"Failed to skip: {str(e)}", ephemeral=True)

            async def loop_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    await interaction.followup.send("You must be in a voice channel to use this!", ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    await interaction.followup.send("You must be in the same voice channel as the bot!", ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    await interaction.followup.send("Nothing is currently playing!", ephemeral=True)
                    return

                try:
                    vc.queue.loop = not vc.queue.loop
                    await interaction.followup.send(f"🔁 Loop {'enabled' if vc.queue.loop else 'disabled'}!", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"Failed to toggle loop: {str(e)}", ephemeral=True)

        # Delete previous now playing message if it exists
        if ctx.guild.id in self.now_playing_messages:
            try:
                await self.now_playing_messages[ctx.guild.id].delete()
            except:
                pass

        # Send new now playing message and store it
        message = await ctx.send(embed=embed, view=MusicControls())
        self.now_playing_messages[ctx.guild.id] = message

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx):
        """Show the currently playing song"""
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

        track = vc.track
        await self.create_now_playing_embed(ctx, track)

async def setup(bot):
    await bot.add_cog(NowPlaying(bot)) 