import discord
from discord.ext import commands
import json

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: kick",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!kick <user> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!kick @user`\n`!kick @user Spamming`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if the user can be kicked
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: kick",
                    description="You cannot kick a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Kick the user
            await member.kick(reason=reason)
            
            # Create embed
            embed = discord.Embed(
                description=f"**Kicked** {member.mention}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: kick",
                description="I don't have permission to kick users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: kick",
                description=f"An error occurred while trying to kick the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: kick",
                description="You don't have the required permission: `Kick Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: kick",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Kick(bot))