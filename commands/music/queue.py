import discord
from discord.ext import commands
import wavelink

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="queue")
    async def queue(self, ctx):
        """Show the current queue"""
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
            # Create queue embed
            queue_embed = discord.Embed(
                title="Music Queue",
                description=""
            )
            
            # Add author with bot's avatar
            queue_embed.set_author(
                name=ctx.guild.me.display_name,
                icon_url=ctx.guild.me.display_avatar.url
            )

            # Add current song
            current_track = vc.track
            if current_track:
                duration = str(current_track.duration).split('.')[0] if hasattr(current_track, 'duration') else "Unknown"
                queue_embed.add_field(
                    name="Now Playing",
                    value=f"**{current_track.title}**\nArtist: {current_track.author if hasattr(current_track, 'author') else 'Unknown'}\nDuration: {duration}",
                    inline=False
                )

            # Add queue
            if not vc.queue.is_empty:
                queue_list = []
                for i, track in enumerate(vc.queue, 1):
                    duration = str(track.duration).split('.')[0] if hasattr(track, 'duration') else "Unknown"
                    queue_list.append(f"**{i}.** {track.title}\nArtist: {track.author if hasattr(track, 'author') else 'Unknown'}\nDuration: {duration}\n")
                
                # Split queue into chunks if it's too long
                queue_text = "\n".join(queue_list)
                if len(queue_text) > 1024:
                    chunks = [queue_text[i:i+1024] for i in range(0, len(queue_text), 1024)]
                    for i, chunk in enumerate(chunks):
                        queue_embed.add_field(
                            name=f"Queue (Part {i+1})" if i > 0 else "Queue",
                            value=chunk,
                            inline=False
                        )
                else:
                    queue_embed.add_field(
                        name="Queue",
                        value=queue_text,
                        inline=False
                    )
            else:
                queue_embed.add_field(
                    name="Queue",
                    value="No songs in queue",
                    inline=False
                )

            # Add queue info
            queue_embed.set_footer(text=f"Total songs in queue: {len(vc.queue)}")
            
            await ctx.send(embed=queue_embed)
        except Exception as e:
            error_embed.description = f"An error occurred: {str(e)}"
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Queue(bot)) 