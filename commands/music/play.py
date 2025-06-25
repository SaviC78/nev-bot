import discord
from discord.ext import commands
import wavelink

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.now_playing_messages = {}  # Store now playing messages per guild

    async def update_voice_status(self, vc: wavelink.Player, track=None):
        """Update the voice channel status with current song information"""
        if not vc or not vc.channel:
            return

        try:
            # Get the channel directly from the guild
            channel = vc.guild.get_channel(vc.channel.id)
            if not channel:
                return

            if track and vc.playing:
                # Use a simple status message
                await channel.edit(topic="Music is playing")
            else:
                # Remove status completely when no music is playing
                await channel.edit(topic="")
        except Exception as e:
            print(f"Failed to update voice status: {e}")
            # Print more detailed error information
            print(f"Channel ID: {vc.channel.id}")
            print(f"Channel Type: {type(vc.channel)}")
            print(f"Guild ID: {vc.guild.id}")

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
            # Convert duration to minutes and seconds
            duration_seconds = int(track.duration.total_seconds())
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration_str = f"{minutes}:{seconds:02d}"  # Format as MM:SS
            embed.add_field(
                name="Duration",
                value=duration_str,
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
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog

                # Create pause button
                self.pause_button = discord.ui.Button(
                    emoji="⏸️",
                    style=discord.ButtonStyle.grey,
                    custom_id="pause"
                )
                self.pause_button.callback = self.pause_callback
                self.add_item(self.pause_button)

                # Create skip button
                self.skip_button = discord.ui.Button(
                    emoji="⏭️",
                    style=discord.ButtonStyle.grey,
                    custom_id="skip"
                )
                self.skip_button.callback = self.skip_callback
                self.add_item(self.skip_button)

                # Create loop button
                self.loop_button = discord.ui.Button(
                    emoji="🔁",
                    style=discord.ButtonStyle.grey,
                    custom_id="loop"
                )
                self.loop_button.callback = self.loop_callback
                self.add_item(self.loop_button)

            async def pause_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    error_embed = discord.Embed(description="You must be in a voice channel to use this!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    error_embed = discord.Embed(description="You must be in the same voice channel as the bot!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    error_embed = discord.Embed(description="Nothing is currently playing!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                try:
                    if vc.paused:
                        # Send response first
                        success_embed = discord.Embed(description="▶️ Resumed!")
                        await interaction.followup.send(embed=success_embed, ephemeral=True)
                        
                        await vc.pause(False)  # Resume
                        self.pause_button.emoji = "⏸️"
                        self.pause_button.custom_id = "pause"
                        await interaction.message.edit(view=self)
                    else:
                        # Send response first
                        success_embed = discord.Embed(description="⏸️ Paused!")
                        await interaction.followup.send(embed=success_embed, ephemeral=True)
                        
                        await vc.pause(True)  # Pause
                        self.pause_button.emoji = "▶️"
                        self.pause_button.custom_id = "resume"
                        await interaction.message.edit(view=self)
                except Exception as e:
                    error_embed = discord.Embed(description=f"Failed to toggle pause state: {str(e)}")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

            async def skip_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    error_embed = discord.Embed(description="You must be in a voice channel to use this!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    error_embed = discord.Embed(description="You must be in the same voice channel as the bot!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    error_embed = discord.Embed(description="Nothing is currently playing!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                try:
                    # Send response first
                    success_embed = discord.Embed(description="⏭️ Skipped!")
                    await interaction.followup.send(embed=success_embed, ephemeral=True)

                    # Get the next track before stopping the current one
                    next_track = None
                    if not vc.queue.is_empty:
                        next_track = await vc.queue.get_wait()
                    
                    # Stop current track
                    await vc.stop()
                    
                    # If there's a next track, play it
                    if next_track:
                        await vc.play(next_track)
                        # Get the cog instance to create the now playing embed
                        music_cog = interaction.client.get_cog("Play")
                        if music_cog:
                            # Delete old now playing message if it exists
                            if interaction.guild.id in music_cog.now_playing_messages:
                                try:
                                    await music_cog.now_playing_messages[interaction.guild.id].delete()
                                except:
                                    pass
                            # Create new now playing embed
                            await music_cog.create_now_playing_embed(await interaction.client.get_context(interaction.message), next_track)
                except Exception as e:
                    error_embed = discord.Embed(description=f"Failed to skip: {str(e)}")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

            async def loop_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                if not interaction.user.voice:
                    error_embed = discord.Embed(description="You must be in a voice channel to use this!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return
                
                if interaction.user.voice.channel != interaction.guild.voice_client.channel:
                    error_embed = discord.Embed(description="You must be in the same voice channel as the bot!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                vc: wavelink.Player = interaction.guild.voice_client
                if not vc.playing:
                    error_embed = discord.Embed(description="Nothing is currently playing!")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                    return

                try:
                    vc.queue.loop = not vc.queue.loop
                    success_embed = discord.Embed(description=f"🔁 Loop {'enabled' if vc.queue.loop else 'disabled'}!")
                    await interaction.followup.send(embed=success_embed, ephemeral=True)
                except Exception as e:
                    error_embed = discord.Embed(description=f"Failed to toggle loop: {str(e)}")
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Delete previous now playing message if it exists
        if ctx.guild.id in self.now_playing_messages:
            try:
                await self.now_playing_messages[ctx.guild.id].delete()
            except:
                pass

        # Send new now playing message and store it
        message = await ctx.send(embed=embed, view=MusicControls(self))
        self.now_playing_messages[ctx.guild.id] = message

    @commands.command(name="play")
    async def play(self, ctx, *, query: str = None):
        """Play a song or playlist"""
        # Create error embed
        error_embed = discord.Embed(
            title="Error",
            description=""
        )

        # Check if user is in a voice channel
        if not ctx.author.voice:
            error_embed.description = "You must be in a voice channel to use this command!"
            return await ctx.send(embed=error_embed)

        # Check if query is provided
        if not query:
            error_embed.description = "Please provide a song name or URL to play!"
            return await ctx.send(embed=error_embed)

        # Get or create the player
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        # Search for the track
        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                error_embed.description = "No tracks found! Please try a different search term."
                return await ctx.send(embed=error_embed)

            track = tracks[0]
            await vc.queue.put_wait(track)
            
            if not vc.playing:
                await vc.play(vc.queue.get())
                await self.create_now_playing_embed(ctx, track)
            else:
                # Create queue embed
                queue_embed = discord.Embed(
                    title="Added to Queue",
                    description=f"**{track.title}**"
                )
                
                # Add author with bot's avatar
                queue_embed.set_author(
                    name=ctx.guild.me.display_name,
                    icon_url=ctx.guild.me.display_avatar.url
                )
                
                # Add track details
                if hasattr(track, 'author'):
                    queue_embed.add_field(
                        name="Artist",
                        value=track.author,
                        inline=True
                    )
                
                # Add duration if available
                if hasattr(track, 'duration'):
                    duration = str(track.duration).split('.')[0]  # Remove milliseconds
                    queue_embed.add_field(
                        name="Duration",
                        value=duration,
                        inline=True
                    )
                
                # Add thumbnail (cover image) if available
                if hasattr(track, 'artwork'):
                    queue_embed.set_thumbnail(url=track.artwork)
                
                await ctx.send(embed=queue_embed)

        except Exception as e:
            error_embed.description = f"An error occurred: {str(e)}"
            await ctx.send(embed=error_embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """Event fired when a track ends."""
        player = payload.player
        if not player:
            return

        # If loop is enabled, play the same track again
        if player.queue.loop:
            await player.play(payload.track)
            return

        # If there are more tracks in the queue, play the next one
        if player.queue:
            next_track = player.queue.get()
            await player.play(next_track)
            
            # Delete old now playing message if it exists
            if player.guild.id in self.now_playing_messages:
                try:
                    old_message = self.now_playing_messages[player.guild.id]
                    await old_message.delete()
                except:
                    pass  # Ignore if message is already deleted
            
            # Create and send new now playing message
            channel = player.channel
            if channel:
                embed = await self.create_now_playing_embed(next_track)
                view = self.MusicControls(self)
                message = await channel.send(embed=embed, view=view)
                self.now_playing_messages[player.guild.id] = message
        else:
            # Queue is empty, stop the player
            await player.stop()
            
            # Delete the now playing message if it exists
            if player.guild.id in self.now_playing_messages:
                try:
                    old_message = self.now_playing_messages[player.guild.id]
                    await old_message.delete()
                except:
                    pass  # Ignore if message is already deleted
                del self.now_playing_messages[player.guild.id]

async def setup(bot):
    await bot.add_cog(Play(bot)) 