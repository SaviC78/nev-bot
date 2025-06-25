import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

class NukeView(discord.ui.View):
    def __init__(self, ctx, channel):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.channel = channel
        self.message = None

    async def on_timeout(self):
        try:
            if self.message:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Channel nuke confirmation timed out.",
                    color=config['embed_colors']['default']
                )
                embed.timestamp = datetime.utcnow()
                await self.message.edit(embed=embed, view=None)
        except discord.errors.NotFound:
            # Channel was deleted, ignore the error
            pass

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        # Store channel settings
        channel_name = self.channel.name
        channel_position = self.channel.position
        channel_category = self.channel.category
        channel_permissions = self.channel.overwrites
        channel_topic = self.channel.topic
        channel_slowmode = self.channel.slowmode_delay
        channel_nsfw = self.channel.nsfw

        # Delete the channel
        await self.channel.delete()

        # Recreate the channel
        new_channel = await channel_category.create_text_channel(
            name=channel_name,
            position=channel_position,
            topic=channel_topic,
            slowmode_delay=channel_slowmode,
            nsfw=channel_nsfw
        )

        # Restore permissions
        for target, overwrite in channel_permissions.items():
            await new_channel.set_permissions(target, overwrite=overwrite)

        # Send nuke confirmation
        embed = discord.Embed(
            title="💥 Channel Nuked",
            description=f"Channel has been nuked by {self.ctx.author.mention}",
            color=config['embed_colors']['default']
        )
        embed.timestamp = datetime.utcnow()
        await new_channel.send(embed=embed)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Cancelled",
            description="Channel nuke has been cancelled.",
            color=config['embed_colors']['default']
        )
        embed.timestamp = datetime.utcnow()
        await interaction.response.edit_message(embed=embed, view=None)

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nuke")
    @commands.has_permissions(manage_messages=True, manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("This command can only be used in text channels!")
            return

        embed = discord.Embed(
            title="⚠️ Channel Nuke Confirmation",
            description=f"Are you sure you want to nuke {ctx.channel.mention}\nThis will delete and recreate the channel with the same settings.",
            color=config['embed_colors']['default']
        )
        embed.timestamp = datetime.utcnow()

        view = NukeView(ctx, ctx.channel)
        view.message = await ctx.send(embed=embed, view=view)

    @nuke.error
    async def nuke_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = []
            if not ctx.author.guild_permissions.manage_messages:
                missing_perms.append("`Manage Messages`")
            if not ctx.author.guild_permissions.manage_channels:
                missing_perms.append("`Manage Channels`")
            
            embed = discord.Embed(
                title="Command: nuke",
                description=f"You don't have the required permissions: {', '.join(missing_perms)}",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Nuke(bot)) 