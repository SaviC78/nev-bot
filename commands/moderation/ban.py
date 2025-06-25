import discord
from discord.ext import commands
import json

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: ban",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!ban <user> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!ban @user`\n`!ban @user Spamming`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if the user can be banned
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: ban",
                    description="You cannot ban a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Ban the user
            await member.ban(reason=reason, delete_message_days=0)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Banned** {member.mention}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: ban",
                description="I don't have permission to ban users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: ban",
                description=f"An error occurred while trying to ban the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: ban",
                description="You don't have the required permission: `Ban Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: ban",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ban(bot)) 