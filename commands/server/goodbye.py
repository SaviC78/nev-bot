import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from variables.user_vars import get_user_vars
from variables.guild_vars import get_guild_vars
from variables.channel_vars import get_channel_vars
from commands.embed.embed import is_valid_url  # Import is_valid_url function
from variables.replace_vars import replace_variables  # Import replace_variables function

def replace_variables(text, ctx):
    """Replace variables in text with their actual values"""
    if not text:
        return text
        
    # Handle both Member objects and context objects
    if isinstance(ctx, discord.Member):
        # If ctx is a Member object, use it directly
        user = ctx
        guild = ctx.guild
        channel = None  # No channel for Member objects
    else:
        # If ctx is a context object, get the appropriate values
        guild = ctx.guild if isinstance(ctx, discord.ext.commands.Context) else ctx.guild
        user = ctx.author if isinstance(ctx, discord.ext.commands.Context) else ctx.user
        channel = ctx.channel if isinstance(ctx, discord.ext.commands.Context) else ctx.channel
    
    # Get all variables
    variables = {}
    variables.update(get_user_vars(user))
    variables.update(get_guild_vars(guild))
    if channel:  # Only add channel variables if we have a channel
        variables.update(get_channel_vars(channel))
    
    # Replace all variables, ensuring values are strings
    for var, value in variables.items():
        if value is None:
            text = text.replace(var, "None")
        else:
            text = text.replace(var, str(value))
    
    return text

class GoodbyeResetView(discord.ui.View):
    def __init__(self, goodbye_cog, guild_id, author_id):
        super().__init__()
        self.goodbye_cog = goodbye_cog
        self.guild_id = guild_id
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        # Reset goodbye data
        self.goodbye_cog.goodbye_data[self.guild_id] = {
            "channel_id": None,
            "embed_name": None,
            "enabled": False
        }
        self.goodbye_cog.save_goodbye_data()

        embed = discord.Embed(
            description="Goodbye settings have been reset!",
            color=self.goodbye_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        embed = discord.Embed(
            description="Goodbye settings reset cancelled!",
            color=self.goodbye_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

class GoodbyeChannelChangeView(discord.ui.View):
    def __init__(self, goodbye_cog, guild_id, new_channel, author_id):
        super().__init__()
        self.goodbye_cog = goodbye_cog
        self.guild_id = guild_id
        self.new_channel = new_channel
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        # Update goodbye channel
        self.goodbye_cog.goodbye_data[self.guild_id]["channel_id"] = self.new_channel.id
        self.goodbye_cog.save_goodbye_data()

        embed = discord.Embed(
            description=f"Goodbye channel has been changed to {self.new_channel.mention}!",
            color=self.goodbye_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You are not the author of this command!", ephemeral=True)
            return

        embed = discord.Embed(
            description="Goodbye channel change cancelled!",
            color=self.goodbye_cog.config['embed_colors']['default']
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.defer()

class Goodbye(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.goodbye_data = {}
        self.load_goodbye_data()
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def load_goodbye_data(self):
        """Load goodbye data from file"""
        if os.path.exists('data/guilds/goodbye.json'):
            with open('data/guilds/goodbye.json', 'r') as f:
                self.goodbye_data = json.load(f)
        else:
            self.goodbye_data = {}

    def save_goodbye_data(self):
        """Save goodbye data to file"""
        os.makedirs('data/guilds', exist_ok=True)
        with open('data/guilds/goodbye.json', 'w') as f:
            json.dump(self.goodbye_data, f, indent=4)

    @commands.hybrid_command(name="goodbye")
    async def goodbye(self, ctx, action: str = None, *, channel: discord.TextChannel = None):
        """Goodbye command for managing goodbye messages"""
        if not action:
            # Show help embed
            embed = discord.Embed(
                title="Goodbye Command Help",
                description="Manage goodbye messages for your server",
                color=self.config['embed_colors']['default']
            )
            embed.add_field(
                name="Usage",
                value="`!goodbye <action> [channel]`",
                inline=False
            )
            embed.add_field(
                name="Actions",
                value=(
                    "`set` - Set the goodbye channel\n"
                    "`message` - Choose an embed for goodbye messages\n"
                    "`view` - Preview the goodbye message\n"
                    "`enable/disable` - Enable/disable goodbye messages\n"
                    "`reset` - Reset all goodbye settings\n"
                    "`config` - View current goodbye configuration"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.goodbye_data:
            self.goodbye_data[guild_id] = {
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
            current_channel_id = self.goodbye_data[guild_id]["channel_id"]
            if current_channel_id:
                current_channel = ctx.guild.get_channel(current_channel_id)
                if current_channel:
                    embed = discord.Embed(
                        title="Change Goodbye Channel",
                        description=f"Current goodbye channel is {current_channel.mention}\nAre you sure you want to change it to {channel.mention}?",
                        color=self.config['embed_colors']['default']
                    )
                    view = GoodbyeChannelChangeView(self, guild_id, channel, ctx.author.id)
                    await ctx.send(embed=embed, view=view, ephemeral=True)
                    return
                else:
                    # Channel exists in data but not in guild, so we can set it directly
                    self.goodbye_data[guild_id]["channel_id"] = channel.id
                    self.save_goodbye_data()
                    embed = discord.Embed(
                        description=f"Goodbye channel set to {channel.mention}!",
                        color=self.config['embed_colors']['default']
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return
            
            # If no channel is set, set it directly
            self.goodbye_data[guild_id]["channel_id"] = channel.id
            self.save_goodbye_data()
            embed = discord.Embed(
                description=f"Goodbye channel set to {channel.mention}!",
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
            view = GoodbyeEmbedSelectView(embed_files, self)
            embed = discord.Embed(
                description="Select an embed for goodbye messages:",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, view=view, ephemeral=True)

        elif action.lower() == "view":
            if not self.goodbye_data[guild_id]["channel_id"]:
                embed = discord.Embed(
                    description="No goodbye channel set! Use `!goodbye set #channel` first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            if not self.goodbye_data[guild_id]["embed_name"]:
                embed = discord.Embed(
                    description="No goodbye embed selected! Use `!goodbye message` first.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Get the channel first
            channel = ctx.guild.get_channel(self.goodbye_data[guild_id]["channel_id"])
            if not channel:
                embed = discord.Embed(
                    description="The goodbye channel no longer exists! Please set a new goodbye channel using `!goodbye set #channel`.",
                    color=self.config['embed_colors']['default']
                )
                await ctx.send(embed=embed, ephemeral=True)
                return

            # Load and send the goodbye message as a preview
            await self.send_goodbye_message(ctx.guild, ctx.author, is_preview=True)
            
            # Send confirmation with channel mention
            embed = discord.Embed(
                description=f"Preview sent to the goodbye channel! {channel.mention}",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, ephemeral=True)

        elif action.lower() in ["enable", "disable"]:
            self.goodbye_data[guild_id]["enabled"] = (action.lower() == "enable")
            self.save_goodbye_data()
            status = "enabled" if action.lower() == "enable" else "disabled"
            embed = discord.Embed(
                description=f"Goodbye messages have been {status}!",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed, ephemeral=True)

        elif action.lower() == "reset":
            embed = discord.Embed(
                title="Reset Goodbye Settings",
                description="Are you sure you want to reset all goodbye settings? This will remove the goodbye channel and embed settings.",
                color=self.config['embed_colors']['default']
            )
            view = GoodbyeResetView(self, guild_id, ctx.author.id)
            await ctx.send(embed=embed, view=view, ephemeral=True)

        elif action.lower() == "config":
            # Get current configuration
            channel_id = self.goodbye_data[guild_id]["channel_id"]
            embed_name = self.goodbye_data[guild_id]["embed_name"]
            enabled = self.goodbye_data[guild_id]["enabled"]

            # Create config embed
            embed = discord.Embed(
                title="Goodbye Configuration",
                description="Current goodbye message settings for this server",
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
            embed.add_field(name="Goodbye Channel", value=channel_info, inline=False)

            # Add embed field
            if embed_name:
                embed_info = f"`{embed_name[:-5]}`"  # Remove .json extension
            else:
                embed_info = "❌ Not set"
            embed.add_field(name="Goodbye Embed", value=embed_info, inline=False)

            await ctx.send(embed=embed, ephemeral=True)

    async def send_goodbye_message(self, guild, member, is_preview=False):
        """Send goodbye message to the goodbye channel"""
        guild_id = str(guild.id)
        if guild_id not in self.goodbye_data:
            return

        if not self.goodbye_data[guild_id]["enabled"] and not is_preview:
            return

        channel_id = self.goodbye_data[guild_id]["channel_id"]
        embed_name = self.goodbye_data[guild_id]["embed_name"]

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
    async def on_member_remove(self, member):
        """Send goodbye message when a member leaves"""
        await self.send_goodbye_message(member.guild, member)

class GoodbyeEmbedSelect(discord.ui.Select):
    def __init__(self, embed_files, goodbye_cog):
        options = []
        for file in embed_files:
            name = file.replace('.json', '')
            options.append(discord.SelectOption(label=name, value=file))
        super().__init__(placeholder="Select an embed for goodbye messages", options=options)
        self.goodbye_cog = goodbye_cog

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        self.goodbye_cog.goodbye_data[guild_id]["embed_name"] = self.values[0]
        self.goodbye_cog.save_goodbye_data()
        
        embed = discord.Embed(
            description=f"Goodbye embed set to `{self.values[0]}`!",
            color=self.goodbye_cog.config['embed_colors']['default']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GoodbyeEmbedSelectView(discord.ui.View):
    def __init__(self, embed_files, goodbye_cog):
        super().__init__()
        self.add_item(GoodbyeEmbedSelect(embed_files, goodbye_cog))

async def setup(bot):
    await bot.add_cog(Goodbye(bot)) 