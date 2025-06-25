import discord
from discord.ext import commands
import json
import re
from datetime import datetime, timedelta

class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def parse_duration(self, duration_str):
        """Parse duration string into timedelta"""
        # Match patterns like "5m", "2h", "1d", etc.
        match = re.match(r'^(\d+)([mhd])$', duration_str.lower())
        if not match:
            return None
            
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        return None

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member = None, duration: str = "5m", *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: timeout",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!timeout <user> [duration] [reason]`",
                inline=False
            )
            embed.add_field(
                name="Duration Format",
                value="`5m` - 5 minutes (default)\n`2h` - 2 hours\n`1d` - 1 day",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!timeout @user` (5 minutes)\n`!timeout @user 2h Spamming`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Parse duration
            duration_delta = self.parse_duration(duration)
            if not duration_delta:
                embed = discord.Embed(
                    title="Command: timeout",
                    description="Invalid duration format. Use: 5m, 2h, 1d",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Check if the user can be timed out
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: timeout",
                    description="You cannot timeout a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Calculate timeout end time using timezone-aware datetime
            timeout_until = discord.utils.utcnow() + duration_delta
            
            # Apply timeout
            await member.timeout(timeout_until, reason=reason)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Timed** out {member.mention} for {duration}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:F>", inline=False)
            embed.add_field(name="Duration", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: timeout",
                description="I don't have permission to timeout users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: timeout",
                description=f"An error occurred while trying to timeout the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @timeout.error
    async def timeout_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: timeout",
                description="You don't have the required permission: `Timeout Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: timeout",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Timeout(bot)) 