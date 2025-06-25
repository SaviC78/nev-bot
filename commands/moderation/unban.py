import discord
from discord.ext import commands
import json

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int = None, *, reason: str = None):
        if user_id is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: unban",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!unban <user_id> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!unban 123456789`\n`!unban 123456789 User reformed`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Get the banned user
            banned_users = [entry async for entry in ctx.guild.bans()]
            user = discord.utils.get(banned_users, user__id=user_id)
            
            if user is None:
                embed = discord.Embed(
                    title="Command: unban",
                    description="Could not find a banned user with that ID.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Unban the user
            await ctx.guild.unban(user.user, reason=reason)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Unbanned** {user.user}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: unban",
                description="I don't have permission to unban users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: unban",
                description=f"An error occurred while trying to unban the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: unban",
                description="You don't have the required permission: `Ban Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: unban",
                description="Please provide a valid user ID.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Unban(bot)) 