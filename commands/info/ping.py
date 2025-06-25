import discord
from discord.ext import commands
import time
from datetime import datetime, timedelta
import json

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def get_uptime(self):
        current_time = time.time()
        difference = int(current_time - self.start_time)
        days = difference // (24 * 3600)
        hours = (difference % (24 * 3600)) // 3600
        minutes = (difference % 3600) // 60
        seconds = difference % 60
        
        return f"{days}d {hours}h {minutes}m {seconds}s"

    @commands.command(name="ping")
    async def ping(self, ctx):
        # Get the bot's latency in milliseconds
        latency = round(self.bot.latency * 1000)
        
        # Get API latency
        before = time.monotonic()
        message = await ctx.send("Pinging...")
        after = time.monotonic()
        api_latency = round((after - before) * 1000)
        
        # Create the embed
        embed = discord.Embed(
            title="Bot Status",
            color=self.config['embed_colors']['default']
        )
        
        # Add fields
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Uptime", value=self.get_uptime(), inline=True)
        
        # Set the bot's avatar as the thumbnail
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Add timestamp
        embed.timestamp = datetime.utcnow()
        
        # Edit the original message with the embed
        await message.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
