import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
import time

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def get_time_ago(self, timestamp):
        now = datetime.now(timezone.utc)
        diff = now - timestamp
        days = diff.days
        if days == 0:
            return "today"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"

    @commands.command(name="info")
    async def info(self, ctx, *, member: discord.Member = None):
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author

        # Create the embed
        embed = discord.Embed(
            color=self.config['embed_colors']['default']
        )

        # Set author
        embed.set_author(name=f"{member.name} ({member.id})")

        # Set thumbnail
        if member.guild_avatar:
            embed.set_thumbnail(url=member.guild_avatar.url)
        else:
            embed.set_thumbnail(url=member.display_avatar.url)

        # Get dates
        created_at = member.created_at
        joined_at = member.joined_at

        # Format dates
        created_str = created_at.strftime("%m/%d/%Y, %I:%M %p")
        joined_str = joined_at.strftime("%m/%d/%Y, %I:%M %p")

        # Get roles
        roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
        roles_str = ", ".join(roles) if roles else "No roles"

        # Build description
        description = f"**Dates**\n"
        description += f"**Created:** {created_str} (<t:{int(created_at.timestamp())}:R>)\n"
        description += f"**Joined:** {joined_str} (<t:{int(joined_at.timestamp())}:R>)\n\n"
        description += f"**Roles ({len(roles)})**\n{roles_str}"

        embed.description = description

        # Get join position
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        join_position = members.index(member) + 1

        # Get mutual servers
        mutual_servers = sum(1 for guild in self.bot.guilds if guild.get_member(member.id))

        # Set footer
        embed.set_footer(text=f"Join position: {join_position}  ∙  {mutual_servers} mutual servers")

        # Send the embed
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot)) 