import discord
from discord.ext import commands
import json

class Untimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member = None, *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: untimeout",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!untimeout <user> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!untimeout @user`\n`!untimeout @user Timeout expired`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if the user is timed out
            if member.timed_out_until is None:
                embed = discord.Embed(
                    title="Command: untimeout",
                    description="This user is not timed out.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Check if the user can be untimed out
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: untimeout",
                    description="You cannot untimeout a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Remove timeout
            await member.timeout(None, reason=reason)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Removed timeout** from {member.mention}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: untimeout",
                description="I don't have permission to remove timeouts.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: untimeout",
                description=f"An error occurred while trying to remove the timeout: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @untimeout.error
    async def untimeout_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: untimeout",
                description="You don't have the required permission: `Timeout Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: untimeout",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Untimeout(bot)) 