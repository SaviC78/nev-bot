import discord
from discord.ext import commands
import json

class Hardban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="hardban")
    @commands.has_permissions(ban_members=True)
    async def hardban(self, ctx, member: discord.Member = None, *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: hardban",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!hardban <user> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!hardban @user`\n`!hardban @user Spamming`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if the user can be banned
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: hardban",
                    description="You cannot hardban a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Ban the user with message history deletion
            await member.ban(reason=reason, delete_message_days=7)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Hardbanned** {member.mention}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: hardban",
                description="I don't have permission to ban users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: hardban",
                description=f"An error occurred while trying to ban the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @hardban.error
    async def hardban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: hardban",
                description="You don't have the required permission: `Ban Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: hardban",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hardban(bot)) 