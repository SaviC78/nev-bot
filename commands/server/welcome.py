import discord
from discord.ext import commands
import json
import os
from variables.user_vars import get_user_vars
from variables.guild_vars import get_guild_vars
from variables.channel_vars import get_channel_vars
from variables.replace_vars import replace_variables
from commands.embed.embed import is_valid_url
from datetime import datetime

class WelcomeResetView(discord.ui.View):
    def __init__(self, welcome_cog, guild_id, author_id):
        super().__init__()
        self.welcome_cog = welcome_cog
        self.guild_id = guild_id
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        # Reset welcome data
        self.welcome_cog.welcome_data[self.guild_id] = {
            "channel_id": None,
            "embed_name": None,
            "enabled": False
        }
        self.welcome_cog.save_welcome_data()

        embed = discord.Embed(
            description="Welcome settings have been reset!",
            color=self.welcome_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        embed = discord.Embed(
            description="Welcome settings reset cancelled!",
            color=self.welcome_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

class WelcomeChannelChangeView(discord.ui.View):
    def __init__(self, welcome_cog, guild_id, new_channel, author_id):
        super().__init__()
        self.welcome_cog = welcome_cog
        self.guild_id = guild_id
        self.new_channel = new_channel
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        # Update welcome channel
        self.welcome_cog.welcome_data[self.guild_id]["channel_id"] = self.new_channel.id
        self.welcome_cog.save_welcome_data()

        embed = discord.Embed(
            description=f"Welcome channel has been changed to {self.new_channel.mention}!",
            color=self.welcome_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        embed = discord.Embed(
            description="Welcome channel change cancelled!",
            color=self.welcome_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_data = {}
        self.load_welcome_data()
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def load_welcome_data(self):
        """Load welcome data from file"""
        if os.path.exists('data/guilds/welcome.json'):
            with open('data/guilds/welcome.json', 'r') as f:
                self.welcome_data = json.load(f)
        else:
            self.welcome_data = {}

    def save_welcome_data(self):
        """Save welcome data to file"""
        os.makedirs('data/guilds', exist_ok=True)
        with open('data/guilds/welcome.json', 'w') as f:
            json.dump(self.welcome_data, f, indent=4)

    @commands.hybrid_command(name="welcome")
    async def welcome(self, ctx, action: str = None, *, channel: discord.TextChannel = None):
        """Welcome command for managing welcome messages"""
        if not action:
            # Show help embed
            embed = discord.Embed(
                title="Welcome Command Help",
                description="Manage welcome messages for your server",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!welcome <action> [channel]`",
                inline=False
            )
            embed.add_field(
                name="Actions",
                value=(
                    "`set` - Set the welcome channel\n"
                    "`message` - Choose an embed for welcome messages\n"
                    "`view` - Preview the welcome message\n"
                    "`enable/disable` - Enable/disable welcome messages\n"
                    "`reset` - Reset all welcome settings\n"
                    "`config` - View current welcome configuration"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.welcome_data:
            self.welcome_data[guild_id] = {
                "channel_id": None,
                "embed_name": None,
                "enabled": False
            }

        if action.lower() == "set":
            if not channel:
                embed = discord.Embed(
                    description="Please specify a channel!",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            # Check if a channel is already set
            current_channel_id = self.welcome_data[guild_id]["channel_id"]
            if current_channel_id:
                current_channel = ctx.guild.get_channel(current_channel_id)
                if current_channel:
                    embed = discord.Embed(
                        title="Change Welcome Channel",
                        description=f"Current welcome channel is {current_channel.mention}\nAre you sure you want to change it to {channel.mention}?",
                        color=self.config['embed_colors']['default']
                    )
                    view = WelcomeChannelChangeView(self, guild_id, channel, ctx.author.id)
                    await ctx.send(embed=embed, view=view, ephemeral=True)
                    return
                else:
                    # Channel exists in data but not in guild, so we can set it directly
                    self.welcome_data[guild_id]["channel_id"] = channel.id
                    self.save_welcome_data()
                    embed = discord.Embed(
                        description=f"Welcome channel set to {channel.mention}!",
                        color=self.config['embed_colors']['default']
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return
            
            # If no channel is set, set it directly
            self.welcome_data[guild_id]["channel_id"] = channel.id
            self.save_welcome_data()
            embed = discord.Embed(
                description=f"Welcome channel set to {channel.mention}!",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, ephemeral=True)

        elif action.lower() == "message":
            # Check if embeds directory exists
            guild_embeds_dir = f'data/guilds/embeds/{ctx.guild.id}'
            if not os.path.exists(guild_embeds_dir):
                embed = discord.Embed(
                    description="No saved embeds found! Use `!ec` to create an embed first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Get list of saved embeds
            embed_files = [f for f in os.listdir(guild_embeds_dir) if f.endswith('.json')]
            if not embed_files:
                embed = discord.Embed(
                    description="No saved embeds found! Use `!ec` to create an embed first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Create view with dropdown
            view = WelcomeEmbedSelectView(embed_files, self)
            embed = discord.Embed(
                description="Select an embed for welcome messages:",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, view=view, ephemeral=True)

        elif action.lower() == "view":
            if not self.welcome_data[guild_id]["channel_id"]:
                embed = discord.Embed(
                    description="No welcome channel set! Use `!welcome set #channel` first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            if not self.welcome_data[guild_id]["embed_name"]:
                embed = discord.Embed(
                    description="No welcome embed selected! Use `!welcome message` first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Get the channel first
            channel = ctx.guild.get_channel(self.welcome_data[guild_id]["channel_id"])
            if not channel:
                embed = discord.Embed(
                    description="The welcome channel no longer exists! Please set a new welcome channel using `!welcome set #channel`.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Load and send the welcome message as a preview
            await self.send_welcome_message(ctx.guild, ctx.author, is_preview=True)
            
            # Send confirmation with channel mention
            embed = discord.Embed(
                description=f"Preview sent to the welcome channel! {channel.mention}",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, ephemeral=True)

        elif action.lower() in ["enable", "disable"]:
            self.welcome_data[guild_id]["enabled"] = (action.lower() == "enable")
            self.save_welcome_data()
            status = "enabled" if action.lower() == "enable" else "disabled"
            embed = discord.Embed(
                description=f"Welcome messages have been {status}!",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, ephemeral=True)

        elif action.lower() == "reset":
            embed = discord.Embed(
                title="Reset Welcome Settings",
                description="Are you sure you want to reset all welcome settings? This will remove the welcome channel and embed settings.",
                color=self.config['embed_colors']['default']
            )
            view = WelcomeResetView(self, guild_id, ctx.author.id)
            await ctx.send(embed=embed, view=view, ephemeral=True)

        elif action.lower() == "config":
            # Get current configuration
            channel_id = self.welcome_data[guild_id]["channel_id"]
            embed_name = self.welcome_data[guild_id]["embed_name"]
            enabled = self.welcome_data[guild_id]["enabled"]

            # Create config embed
            embed = discord.Embed(
                title="Welcome Configuration",
                description="Current welcome message settings for this server",
                color=self.config['embed_colors']['default']
            )

            # Add status field
            status = "✅ Enabled" if enabled else "❌ Disabled"
            embed.add_field(name="Status", value=status, inline=False)

            # Add channel field
            if channel_id:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    channel_info = f"{channel.mention} (`{channel.name}`)"
                else:
                    channel_info = "❌ Channel no longer exists"
            else:
                channel_info = "❌ Not set"
            embed.add_field(name="Welcome Channel", value=channel_info, inline=False)

            # Add embed field
            if embed_name:
                embed_info = f"`{embed_name[:-5]}`"  # Remove .json extension
            else:
                embed_info = "❌ Not set"
            embed.add_field(name="Welcome Embed", value=embed_info, inline=False)

            await ctx.send(embed=embed, ephemeral=True)

    async def send_welcome_message(self, guild, member, is_preview=False):
        """Send welcome message to the welcome channel"""
        guild_id = str(guild.id)
        if guild_id not in self.welcome_data:
            return

        if not self.welcome_data[guild_id]["enabled"] and not is_preview:
            return

        channel_id = self.welcome_data[guild_id]["channel_id"]
        embed_name = self.welcome_data[guild_id]["embed_name"]

        if not channel_id or not embed_name:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        # Load embed data
        guild_embeds_dir = f'data/guilds/embeds/{guild.id}'
        embed_file = f'{guild_embeds_dir}/{embed_name}'
        
        if not os.path.exists(embed_file):
            return
            
        with open(embed_file, 'r') as f:
            embed_data = json.load(f)
            
        # Create embed
        embed = discord.Embed()
        
        # Set embed fields with variable replacement
        if embed_data.get('title'):
            title = replace_variables(embed_data['title'], member)
            if title and title.strip():
                embed.title = title

        if embed_data.get('description'):
            description = replace_variables(embed_data['description'], member)
            if description and description.strip():
                embed.description = description

        if embed_data.get('color'):
            embed.color = discord.Color(embed_data['color'])

        if embed_data.get('author'):
            author = embed_data['author']
            if author.get('name'):
                name = replace_variables(author['name'], member)
                if name and name.strip():
                    icon_url = author.get('icon_url')
                    if icon_url:
                        icon_url = replace_variables(icon_url, member)
                        if not is_valid_url(icon_url):
                            icon_url = None
                    embed.set_author(name=name, icon_url=icon_url)

        if embed_data.get('image'):
            image_url = replace_variables(embed_data['image'], member)
            if image_url and image_url.strip() and is_valid_url(image_url):
                embed.set_image(url=image_url)

        if embed_data.get('thumbnail'):
            thumbnail_url = replace_variables(embed_data['thumbnail'], member)
            if thumbnail_url and thumbnail_url.strip() and is_valid_url(thumbnail_url):
                embed.set_thumbnail(url=thumbnail_url)

        if embed_data.get('footer'):
            footer = embed_data['footer']
            if footer.get('text'):
                text = replace_variables(footer['text'], member)
                if text and text.strip():
                    icon_url = footer.get('icon_url')
                    if icon_url:
                        icon_url = replace_variables(icon_url, member)
                        if not is_valid_url(icon_url):
                            icon_url = None
                    embed.set_footer(text=text, icon_url=icon_url)

        if embed_data.get('timestamp'):
            embed.timestamp = datetime.fromisoformat(embed_data['timestamp'])
            
        # Get message content with variable replacement
        message_content = replace_variables(embed_data.get('message_content', ''), member)
        if not message_content or not message_content.strip():
            message_content = None
        
        # Send embed
        await channel.send(content=message_content, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a member joins"""
        await self.send_welcome_message(member.guild, member)

class WelcomeEmbedSelect(discord.ui.Select):
    def __init__(self, embed_files, welcome_cog):
        options = [
            discord.SelectOption(
                label=filename[:-5],  # Remove .json extension for display
                value=filename  # Keep full filename with .json for storage
            ) for filename in embed_files
        ]
        super().__init__(
            placeholder="Choose an embed for welcome messages",
            options=options,
            min_values=1,
            max_values=1
        )
        self.welcome_cog = welcome_cog

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        self.welcome_cog.welcome_data[guild_id]["embed_name"] = self.values[0]
        self.welcome_cog.save_welcome_data()
        
        embed = discord.Embed(
            title="Welcome Embed Selected",
            description=f"Welcome messages will now use the `{self.values[0][:-5]}` embed!",
            color=self.welcome_cog.config['embed_colors']['default']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class WelcomeEmbedSelectView(discord.ui.View):
    def __init__(self, embed_files, welcome_cog):
        super().__init__()
        self.add_item(WelcomeEmbedSelect(embed_files, welcome_cog))

async def setup(bot):
    await bot.add_cog(Welcome(bot)) 