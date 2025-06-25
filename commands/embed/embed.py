import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from urllib.parse import urlparse, urljoin
from variables.user_vars import get_user_vars
from variables.guild_vars import get_guild_vars
from variables.channel_vars import get_channel_vars
from variables.replace_vars import replace_variables  # Import replace_variables function

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

def replace_variables(text, ctx):
    """Replace variables in text with their actual values"""
    if not text:
        return text
        
    # Get the guild from either context or interaction
    guild = ctx.guild if isinstance(ctx, discord.ext.commands.Context) else ctx.guild
    
    # Get the user from either context or interaction
    user = ctx.author if isinstance(ctx, discord.ext.commands.Context) else ctx.user
    
    # Get the channel from either context or interaction
    channel = ctx.channel if isinstance(ctx, discord.ext.commands.Context) else ctx.channel
    
    # Get all variables
    variables = {}
    variables.update(get_user_vars(user))
    variables.update(get_guild_vars(guild))
    variables.update(get_channel_vars(channel))
    
    # Replace all variables, ensuring values are strings
    for var, value in variables.items():
        if value is None:
            text = text.replace(var, "None")
        else:
            text = text.replace(var, str(value))
    
    return text

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def format_url(url):
    if not url:
        return None
    if url.startswith(('https://cdn.discordapp.com/', 'https://media.discordapp.net/')):
        return url
    if is_valid_url(url):
        return url
    # If it's not a valid URL, assume it's a relative path and add a base URL
    base_url = "https://cdn.discordapp.com/attachments/"
    return urljoin(base_url, url)

class EmbedSelectView(discord.ui.View):
    def __init__(self, embed_files):
        super().__init__()
        self.add_item(EmbedSelect(embed_files))

class EmbedSelect(discord.ui.Select):
    def __init__(self, embed_files):
        options = []
        for file in embed_files:
            name = file.replace('.json', '')
            options.append(discord.SelectOption(label=name, value=file))
        super().__init__(placeholder="Select an embed to send", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Load embed data
        guild_embeds_dir = f'data/guilds/embeds/{interaction.guild_id}'
        with open(f'{guild_embeds_dir}/{self.values[0]}', 'r') as f:
            embed_data = json.load(f)
            
        # Create embed
        embed = discord.Embed()
        
        # Set embed fields with variable replacement
        if embed_data.get('title'):
            embed.title = replace_variables(embed_data['title'], interaction)
        if embed_data.get('description'):
            embed.description = replace_variables(embed_data['description'], interaction)
        if embed_data.get('color'):
            embed.color = discord.Color(embed_data['color'])
        if embed_data.get('author'):
            author = embed_data['author']
            if author.get('name'):
                name = replace_variables(author['name'], interaction)
                icon_url = author.get('icon_url')
                if icon_url:
                    icon_url = replace_variables(icon_url, interaction)
                embed.set_author(name=name, icon_url=icon_url)
        if embed_data.get('image'):
            image_url = replace_variables(embed_data['image'], interaction)
            embed.set_image(url=image_url)
        if embed_data.get('thumbnail'):
            thumbnail_url = replace_variables(embed_data['thumbnail'], interaction)
            embed.set_thumbnail(url=thumbnail_url)
        if embed_data.get('footer'):
            footer = embed_data['footer']
            if footer.get('text'):
                text = replace_variables(footer['text'], interaction)
                icon_url = footer.get('icon_url')
                if icon_url:
                    icon_url = replace_variables(icon_url, interaction)
                embed.set_footer(text=text, icon_url=icon_url)
        if embed_data.get('timestamp'):
            embed.timestamp = datetime.fromisoformat(embed_data['timestamp'])
            
        # Get message content with variable replacement
        message_content = replace_variables(embed_data.get('message_content', ''), interaction)
        
        # Send embed
        await interaction.channel.send(content=message_content, embed=embed)
        
        # Send confirmation embed
        confirm_embed = discord.Embed(
            title="Embed Sent Successfully",
            description=f"The embed has been sent to {interaction.channel.mention}",
            color=config['embed_colors']['default']
        )
        await interaction.response.edit_message(embed=confirm_embed, view=None)

class EmbedDeleteSelect(discord.ui.Select):
    def __init__(self, embeds):
        options = []
        for embed in embeds:
            options.append(discord.SelectOption(
                label=embed,
                value=embed
            ))
        super().__init__(
            placeholder="Select an embed to delete",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_embed = self.values[0]
        embed_path = f'data/guilds/embeds/{interaction.guild_id}/{selected_embed}.json'
        
        try:
            os.remove(embed_path)
            embed = discord.Embed(
                title="✅ Embed Deleted",
                description=f"Successfully deleted embed: `{selected_embed}`",
                color=config['embed_colors']['success']
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to delete embed: {str(e)}",
                color=config['embed_colors']['error']
            )
            await interaction.response.edit_message(embed=embed, view=None)

class EmbedDeleteView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.add_item(EmbedDeleteSelect(embeds))

class EmbedEditView(discord.ui.View):
    def __init__(self, embed: discord.Embed, message_content: str = None):
        super().__init__(timeout=None)
        self.embed = embed
        self.message_content = message_content
        # Initialize embed cache as a dictionary
        self.embed_cache = {
            'title': '',
            'description': '',
            'author_name': '',
            'author_icon': '',
            'image': '',
            'thumbnail': '',
            'footer_text': '',
            'footer_icon': '',
            'message_content': ''
        }

    @discord.ui.select(
        placeholder="Choose an option",
        options=[
            discord.SelectOption(label="Message", description="Set message content"),
            discord.SelectOption(label="Title", description="Set embed title"),
            discord.SelectOption(label="Description", description="Set embed description"),
            discord.SelectOption(label="Image", description="Set main image"),
            discord.SelectOption(label="Thumbnail", description="Set thumbnail image"),
            discord.SelectOption(label="Color", description="Set embed color (hex)"),
            discord.SelectOption(label="Author", description="Set author name and icon"),
            discord.SelectOption(label="Footer", description="Set footer text and icon"),
            discord.SelectOption(label="Time Stamp", description="Toggle timestamp"),
            discord.SelectOption(label="Reset", description="Reset embed to default"),
            discord.SelectOption(label="Save Embed", description="Save this embed for later use")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        option = select.values[0]
        if option == "Message":
            modal = EmbedEditModal(option, self.embed, self.embed_cache)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.value:
                # Replace variables in the message content
                message_content = replace_variables(modal.value, interaction)
                self.message_content = message_content
                await interaction.message.edit(content=self.message_content, embed=self.embed)
        elif option == "Reset":
            # Load default color from config
            with open('config.json', 'r') as f:
                config = json.load(f)
                default_color = config['embed_colors']['default']

            # Create new empty embed
            self.embed = discord.Embed(
                description="‎",  # Use zero-width space character
                color=int(default_color, 16) if isinstance(default_color, str) else default_color
            )
            self.message_content = ""  # Reset message content
            # Clear message content from cache
            self.embed_cache['message_content'] = ""
            await interaction.message.edit(content=self.message_content, embed=self.embed)
            await interaction.response.defer()
        elif option == "Save Embed":
            # Create modal for embed name
            modal = EmbedNameModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            
            if modal.name:
                # Create embeds directory if it doesn't exist
                guild_embeds_dir = f'data/guilds/embeds/{interaction.guild_id}'
                os.makedirs(guild_embeds_dir, exist_ok=True)
                
                # Get raw values from the embed cache
                embed_data = {
                    'title': self.embed_cache.get('title', ''),
                    'description': self.embed_cache.get('description', ''),
                    'color': self.embed.color.value if self.embed.color else None,
                    'author': {
                        'name': self.embed_cache.get('author_name', ''),
                        'icon_url': self.embed_cache.get('author_icon', '')
                    },
                    'image': self.embed_cache.get('image', ''),
                    'thumbnail': self.embed_cache.get('thumbnail', ''),
                    'footer': {
                        'text': self.embed_cache.get('footer_text', ''),
                        'icon_url': self.embed_cache.get('footer_icon', '')
                    },
                    'timestamp': self.embed.timestamp.isoformat() if self.embed.timestamp else None,
                    'message_content': self.embed_cache.get('message_content', '')
                }
                
                # Save to file
                with open(f'{guild_embeds_dir}/{modal.name}.json', 'w') as f:
                    json.dump(embed_data, f, indent=4)
                
                await interaction.followup.send(f"Embed saved as `{modal.name}`!", ephemeral=True)
        else:
            modal = EmbedEditModal(option, self.embed, self.embed_cache)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.value:
                if option == "Title":
                    title = modal.value  # Store raw value with variables
                    if title:  # Only set title if it's not empty
                        # Replace variables in the title
                        title = replace_variables(title, interaction)
                        self.embed.title = title
                    else:
                        self.embed.title = None  # Remove title if empty
                elif option == "Description":
                    description = modal.value  # Store raw value with variables
                    if description:  # Only set description if it's not empty
                        # Replace variables in the description
                        description = replace_variables(description, interaction)
                        # Preserve empty lines at the beginning by adding zero-width spaces
                        lines = description.split('\n')
                        for i, line in enumerate(lines):
                            if not line.strip():  # If line is empty
                                lines[i] = "‎"  # Replace with zero-width space
                        description = '\n'.join(lines)
                        self.embed.description = description
                    else:
                        self.embed.description = "‎"  # Reset to zero-width space if empty
                elif option == "Image":
                    # First replace variables in the URL
                    image_url = replace_variables(modal.value, interaction)
                    # Then validate the URL
                    if image_url and image_url.strip() and is_valid_url(image_url):
                        self.embed.set_image(url=image_url)
                    else:
                        error_embed = discord.Embed(
                            title="❌ Error",
                            description="Invalid image URL! Please provide a valid image URL.",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return
                elif option == "Thumbnail":
                    # First replace variables in the URL
                    thumbnail_url = replace_variables(modal.value, interaction)
                    # Then validate the URL
                    if thumbnail_url and thumbnail_url.strip() and is_valid_url(thumbnail_url):
                        self.embed.set_thumbnail(url=thumbnail_url)
                    else:
                        error_embed = discord.Embed(
                            title="❌ Error",
                            description="Invalid thumbnail URL! Please provide a valid image URL.",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return
                elif option == "Color":
                    try:
                        color = int(modal.value.replace("#", ""), 16)
                        self.embed.color = discord.Color(color)
                    except:
                        error_embed = discord.Embed(
                            title="❌ Error",
                            description="Invalid color hex code! Please provide a valid hex color code (e.g. #FF0000).",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return
                elif option == "Author":
                    name, icon_url = modal.value.split("|")
                    name = name.strip()  # Store raw value with variables
                    icon_url = icon_url.strip() if icon_url.strip() else None
                    if icon_url:
                        icon_url = replace_variables(icon_url, interaction)
                        if not is_valid_url(icon_url):
                            error_embed = discord.Embed(
                                title="❌ Error",
                                description="Invalid author icon URL! Please provide a valid image URL.",
                                color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=error_embed, ephemeral=True)
                            return
                    self.embed.set_author(name=name, icon_url=icon_url)
                elif option == "Footer":
                    text, icon_url = modal.value.split("|")
                    text = text.strip()  # Store raw value with variables
                    icon_url = icon_url.strip() if icon_url.strip() else None
                    if icon_url:
                        icon_url = replace_variables(icon_url, interaction)
                        if not is_valid_url(icon_url):
                            error_embed = discord.Embed(
                                title="❌ Error",
                                description="Invalid footer icon URL! Please provide a valid image URL.",
                                color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=error_embed, ephemeral=True)
                            return
                    # Replace variables in the footer text
                    text = replace_variables(text, interaction)
                    self.embed.set_footer(text=text, icon_url=icon_url)
                elif option == "Time Stamp":
                    if modal.value.lower() == "true":
                        self.embed.timestamp = discord.utils.utcnow()
                    else:
                        self.embed.timestamp = None
                
                await interaction.message.edit(content=self.message_content, embed=self.embed)

class EmbedNameModal(discord.ui.Modal, title="Save Embed"):
    name = discord.ui.TextInput(
        label="Embed Name",
        placeholder="Enter a name for this embed...",
        required=True,
        min_length=1,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

class EmbedEditModal(discord.ui.Modal):
    def __init__(self, option, embed, embed_cache):
        super().__init__(title=f"Edit {option}")
        self.option = option
        self.embed = embed
        self.embed_cache = embed_cache
        self.value = None

        if option == "Message":
            self.add_item(discord.ui.TextInput(
                label="Message Content",
                placeholder="Enter message content...",
                required=False,
                style=discord.TextStyle.paragraph
            ))
        elif option == "Title":
            self.add_item(discord.ui.TextInput(
                label="Title",
                placeholder="Enter embed title...",
                required=False,
                max_length=256
            ))
        elif option == "Description":
            self.add_item(discord.ui.TextInput(
                label="Description",
                placeholder="Enter embed description...",
                required=False,
                style=discord.TextStyle.paragraph
            ))
        elif option == "Image":
            self.add_item(discord.ui.TextInput(
                label="Image URL",
                placeholder="Enter image URL...",
                required=True
            ))
        elif option == "Thumbnail":
            self.add_item(discord.ui.TextInput(
                label="Thumbnail URL",
                placeholder="Enter thumbnail URL...",
                required=True
            ))
        elif option == "Color":
            self.add_item(discord.ui.TextInput(
                label="Color Hex",
                placeholder="Enter color hex code (e.g. #FF0000)...",
                required=True,
                max_length=7
            ))
        elif option == "Author":
            self.add_item(discord.ui.TextInput(
                label="Author Name",
                placeholder="Enter author name...",
                required=True,
                max_length=256
            ))
            self.add_item(discord.ui.TextInput(
                label="Author Icon URL",
                placeholder="Enter author icon URL (optional)...",
                required=False
            ))
        elif option == "Footer":
            self.add_item(discord.ui.TextInput(
                label="Footer Text",
                placeholder="Enter footer text...",
                required=True,
                max_length=2048
            ))
            self.add_item(discord.ui.TextInput(
                label="Footer Icon URL",
                placeholder="Enter footer icon URL (optional)...",
                required=False
            ))
        elif option == "Time Stamp":
            self.add_item(discord.ui.TextInput(
                label="Enable Timestamp",
                placeholder="Enter 'true' to enable timestamp...",
                required=True,
                max_length=5
            ))

    async def on_submit(self, interaction: discord.Interaction):
        if self.option in ["Author", "Footer"]:
            # Combine the two inputs with a pipe separator
            self.value = f"{self.children[0].value}|{self.children[1].value}"
            # Store raw values in cache
            if self.option == "Author":
                self.embed_cache['author_name'] = self.children[0].value
                self.embed_cache['author_icon'] = self.children[1].value
            else:  # Footer
                self.embed_cache['footer_text'] = self.children[0].value
                self.embed_cache['footer_icon'] = self.children[1].value
        else:
            self.value = self.children[0].value
            # Store raw value in cache
            if self.option == "Title":
                self.embed_cache['title'] = self.value
            elif self.option == "Description":
                self.embed_cache['description'] = self.value
            elif self.option == "Image":
                self.embed_cache['image'] = self.value
            elif self.option == "Thumbnail":
                self.embed_cache['thumbnail'] = self.value
            elif self.option == "Message":
                self.embed_cache['message_content'] = self.value
        await interaction.response.defer()

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_cache = {}

    @commands.hybrid_command(name="embed")
    async def embed(self, ctx, action: str = None):
        """Embed command for managing embeds"""
        if not action:
            # Show help embed
            embed = discord.Embed(
                title="Embed Commands",
                description="Available embed commands:",
                color=config['embed_colors']['default']
            )
            embed.add_field(
                name="Create",
                value="`!embed create` - Create a new embed\nAlias: `!ec`",
                inline=False
            )
            embed.add_field(
                name="Send",
                value="`!embed send` - Send a saved embed\nAlias: `!es`",
                inline=False
            )
            embed.add_field(
                name="Delete",
                value="`!embed delete` - Delete a saved embed\nAlias: `!ed`",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        if action.lower() == "create":
            await self.create_embed(ctx)
        elif action.lower() == "send":
            await self.send_embed(ctx)
        elif action.lower() == "delete":
            await self.delete_embed(ctx)

    @commands.hybrid_command(name="ec", aliases=["embed create"])
    async def ec(self, ctx):
        """Create a new embed"""
        await self.create_embed(ctx)

    @commands.hybrid_command(name="es", aliases=["embed send"])
    async def es(self, ctx):
        """Send a saved embed"""
        await self.send_embed(ctx)

    @commands.hybrid_command(name="ed", aliases=["embed delete"])
    async def ed(self, ctx):
        """Delete a saved embed"""
        await self.delete_embed(ctx)

    async def create_embed(self, ctx):
        """Create a new embed"""
        # Load default color from config
        default_color = config['embed_colors']['default']
        default_color_int = int(default_color, 16) if isinstance(default_color, str) else default_color
        
        # Create initial empty embed
        embed = discord.Embed(
            description="‎",  # Zero-width space character
            color=default_color_int
        )
        
        # Create view with edit buttons
        view = EmbedEditView(embed)
        
        # Send the embed with the edit view
        message = await ctx.send(embed=embed, view=view)
        
        # Store the embed in cache
        self.embed_cache[message.id] = embed

    async def send_embed(self, ctx):
        """Send a saved embed"""
        # Check if guild embeds directory exists
        guild_embeds_dir = f'data/guilds/embeds/{ctx.guild.id}'
        if not os.path.exists(guild_embeds_dir):
            embed = discord.Embed(
                title="No Saved Embeds",
                description="You haven't saved any embeds yet. Use `!embed create` to create and save an embed.",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Get list of saved embeds
        embed_files = [f for f in os.listdir(guild_embeds_dir) if f.endswith('.json')]
        if not embed_files:
            embed = discord.Embed(
                title="No Saved Embeds",
                description="You haven't saved any embeds yet. Use `!embed create` to create and save an embed.",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Create view with dropdown
        view = EmbedSelectView(embed_files)
        embed = discord.Embed(
            title="Select an embed to send",
            description="Choose an embed from the dropdown menu below.",
            color=config['embed_colors']['default']
        )
        await ctx.send(embed=embed, view=view, ephemeral=True)

    async def delete_embed(self, ctx):
        """Delete a saved embed"""
        # Check if embeds directory exists
        embeds_dir = f'data/guilds/embeds/{ctx.guild.id}'
        if not os.path.exists(embeds_dir):
            embed = discord.Embed(
                title="❌ No Saved Embeds",
                description="There are no saved embeds to delete.",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
            return

        # Get list of saved embeds
        embeds = [f[:-5] for f in os.listdir(embeds_dir) if f.endswith('.json')]
        if not embeds:
            embed = discord.Embed(
                title="❌ No Saved Embeds",
                description="There are no saved embeds to delete.",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
            return

        # Create and send the select menu
        embed = discord.Embed(
            title="🗑️ Delete Embed",
            description="Select an embed to delete from the dropdown menu below.",
            color=config['embed_colors']['default']
        )
        view = EmbedDeleteView(embeds)
        await ctx.send(embed=embed, view=view)

    @ed.error
    async def ed_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Command: embed delete",
                description="You don't have the required permission: `Administrator`",
                color=config['embed_colors']['error']
            )
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Embed(bot))