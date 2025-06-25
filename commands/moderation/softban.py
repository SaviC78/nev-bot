import discord
from discord.ext import commands
import json

class Softban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="softban")
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member = None, *, reason: str = None):
        if member is None:
            # Show command usage
            embed = discord.Embed(
                title="Command: softban",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!softban <user> [reason]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`!softban @user`\n`!softban @user Spamming`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if the user can be softbanned
            if member.top_role >= ctx.author.top_role:
                embed = discord.Embed(
                    title="Command: softban",
                    description="You cannot softban a user with a higher or equal role.",
                    color=self.config['embed_colors']['error']
                )
                await ctx.send(embed=embed)
                return

            # Softban the user (ban and immediately unban)
            await member.ban(reason=reason, delete_message_days=7)
            await member.unban(reason="Softban complete")
            
            # Create embed
            embed = discord.Embed(
                description=f"**Softbanned** {member.mention}",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Command: softban",
                description="I don't have permission to ban/unban users.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Command: softban",
                description=f"An error occurred while trying to softban the user: {str(e)}",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

    @softban.error
    async def softban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: softban",
                description="You don't have the required permission: `Ban Members`",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Command: softban",
                description="Could not find that user. Please provide a valid user ID, mention, or name.",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Softban(bot)) 