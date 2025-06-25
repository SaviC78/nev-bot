import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class VoiceMasterButtons(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:lock:1361853790432657409>", custom_id="vm_lock")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has a voice channel
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, connect=False)
        embed = discord.Embed(description="🔒 Voice channel has been locked!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:unlock:1361853812050100274>", custom_id="vm_unlock")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, connect=True)
        embed = discord.Embed(description="🔓 Voice channel has been unlocked!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:hide:1361852490709995540>", custom_id="vm_ghost")
    async def ghost_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        embed = discord.Embed(description="👻 Voice channel is now hidden!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:reveal:1361854891554766868>", custom_id="vm_reveal")
    async def reveal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        embed = discord.Embed(description="👁️ Voice channel is now visible!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:claim:1361852362523672846>", custom_id="vm_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels:
            await interaction.response.send_message("This is not a temporary voice channel!", ephemeral=True)
            return
            
        owner_id = self.cog.temp_channels[channel.id]
        
        # Check if the user trying to claim is already the owner
        if interaction.user.id == owner_id:
            embed = discord.Embed(
                description="👑 You're already the owner of this channel!",
                color=self.cog.config['embed_colors']['default']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        owner = interaction.guild.get_member(owner_id)
        
        if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == channel.id:
            embed = discord.Embed(
                description="👑 The owner is still in the channel!",
                color=self.cog.config['embed_colors']['default']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Transfer ownership
        self.cog.temp_channels[channel.id] = interaction.user.id
        await channel.edit(name=f"{interaction.user.display_name}'s channel")
        embed = discord.Embed(description="👑 You are now the owner of this channel!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:disconnect:1361853954698383513>", custom_id="vm_kick")
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        # Create a select menu for choosing the member to disconnect
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in channel.members
            if member != interaction.user
        ]
        
        if not options:
            await interaction.response.send_message("No other members in the channel to disconnect!", ephemeral=True)
            return

        class DisconnectSelect(discord.ui.Select):
            def __init__(self, cog):
                super().__init__(placeholder="Select a member to disconnect", options=options)
                self.cog = cog

            async def callback(self, interaction: discord.Interaction):
                member = interaction.guild.get_member(int(self.values[0]))
                if member:
                    await member.move_to(None)
                    embed = discord.Embed(description=f"🔨 Disconnected {member.mention}!", color=self.cog.config['embed_colors']['default'])
                    await interaction.response.send_message(embed=embed, ephemeral=True)

        view = discord.ui.View()
        view.add_item(DisconnectSelect(self.cog))
        await interaction.response.send_message("Select a member to disconnect:", view=view, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:activity:1361848643962929222>", custom_id="vm_activity")
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        try:
            # Chess in the Park Application ID
            chess_id = "832012774040141894"
            invite = await channel.create_invite(
                target_type=discord.InviteTarget.embedded_application,
                target_application_id=chess_id
            )
            embed = discord.Embed(description=f"🚀 Started Chess in the Park! [Click to join]({invite.url})", color=self.cog.config['embed_colors']['default'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            embed = discord.Embed(description="❌ Failed to start the activity. Please try again.", color=self.cog.config['embed_colors']['error'])
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:information:1361854914707587092>", custom_id="vm_info")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels:
            await interaction.response.send_message("This is not a temporary voice channel!", ephemeral=True)
            return

        owner_id = self.cog.temp_channels[channel.id]
        owner = interaction.guild.get_member(owner_id)
        
        info = [
            f"**Name:** {channel.name}",
            f"**Bitrate:** {channel.bitrate//1000}kbps",
            f"**Region:** {channel.rtc_region or 'Automatic'}",
            f"**Users:** {len(channel.members)}/{channel.user_limit or '∞'}",
            f"**Owner:** {owner.mention if owner else 'Unknown'}",
            f"**Locked:** {'Yes' if not channel.permissions_for(interaction.guild.default_role).connect else 'No'}",
            f"**Hidden:** {'Yes' if not channel.permissions_for(interaction.guild.default_role).view_channel else 'No'}",
            f"**Latency:** {round(interaction.client.latency * 1000)}ms"
        ]
        
        embed = discord.Embed(
            title="Channel Information",
            description="\n".join(info),
            color=self.cog.config['embed_colors']['default']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:Increase:1361849878153527378>", custom_id="vm_increase")
    async def increase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        new_limit = channel.user_limit + 1 if channel.user_limit > 0 else 2
        await channel.edit(user_limit=new_limit)
        embed = discord.Embed(description=f"➕ User limit increased to {new_limit}!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:decrease:1361850052963733616>", custom_id="vm_decrease")
    async def decrease_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        if channel.id not in self.cog.temp_channels or self.cog.temp_channels[channel.id] != interaction.user.id:
            await interaction.response.send_message("You don't own this voice channel!", ephemeral=True)
            return

        new_limit = max(0, channel.user_limit - 1 if channel.user_limit > 0 else 0)
        await channel.edit(user_limit=new_limit)
        limit_text = str(new_limit) if new_limit > 0 else "∞"
        embed = discord.Embed(description=f"➖ User limit decreased to {limit_text}!", color=self.cog.config['embed_colors']['default'])
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoiceMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        # Load data
        self.data_file = 'data/guilds/voicemaster.json'
        if not os.path.exists('data/guilds'):
            os.makedirs('data/guilds')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)
        self.load_data()
        
        # Add persistent view
        self.bot.add_view(VoiceMasterButtons(self))

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.temp_channels = data.get('temp_channels', {})
                self.voice_channels = data.get('voice_channels', {})
        except (json.JSONDecodeError, FileNotFoundError):
            self.temp_channels = {}
            self.voice_channels = {}
            self.save_data()

    def save_data(self):
        data = {
            'temp_channels': self.temp_channels,
            'voice_channels': self.voice_channels
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    @commands.command(name="voicemaster")
    async def voicemaster(self, ctx):
        # Check permissions first
        if not ctx.author.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="Missing Permissions",
                description="You need the `Manage Channels` permission to use this command!",
                color=self.config['embed_colors']['error']
            )
            await ctx.send(embed=embed)
            return

        # Check if voicemaster is already set up
        guild_id = str(ctx.guild.id)
        if guild_id in self.voice_channels:
            try:
                category = self.bot.get_channel(int(self.voice_channels[guild_id]["category_id"]))
                control_panel = self.bot.get_channel(int(self.voice_channels[guild_id]["control_panel_id"]))
                join_channel = self.bot.get_channel(int(self.voice_channels[guild_id]["join_channel_id"]))
                
                if category and control_panel and join_channel:
                    embed = discord.Embed(
                        title="VoiceMaster Already Setup",
                        description=f"VoiceMaster is already set up in this server!\n\nInterface: {control_panel.mention}\nJoin Channel: {join_channel.mention}",
                        color=self.config['embed_colors']['default']
                    )
                    await ctx.send(embed=embed)
                    return
            except (KeyError, ValueError):
                # If any channel is missing, remove the invalid setup
                del self.voice_channels[guild_id]
                self.save_data()

        # Create the initial embed
        embed = discord.Embed(
            title="VoiceMaster Setup",
            description="No VoiceMaster is currently set up in this server. Would you like to set it up?",
            color=self.config['embed_colors']['default']
        )

        # Create buttons
        class SetupButtons(discord.ui.View):
            def __init__(self, cog):
                super().__init__(timeout=60)
                self.cog = cog

            @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
            async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Create category
                category = await interaction.guild.create_category("Voicemaster")
                
                # Create text channel
                control_panel = await interaction.guild.create_text_channel(
                    "interface",
                    category=category,
                    position=0
                )
                
                # Create voice channel
                join_channel = await interaction.guild.create_voice_channel(
                    "Join 2 Create",
                    category=category,
                    position=1
                )

                # Save the setup data
                guild_id = str(interaction.guild.id)
                self.cog.voice_channels[guild_id] = {
                    "category_id": str(category.id),
                    "control_panel_id": str(control_panel.id),
                    "join_channel_id": str(join_channel.id)
                }
                self.cog.save_data()

                # Send interface message
                interface_embed = discord.Embed(
                    title="VoiceMaster Interface",
                    description=f"Use the buttons below to control your voice channel.\n\n"
                               "**Button Usage**\n"
                               f"<:lock:1361853790432657409> — [Lock]({control_panel.jump_url}) the voice channel\n"
                               f"<:unlock:1361853812050100274> — [Unlock]({control_panel.jump_url}) the voice channel\n"
                               f"<:hide:1361852490709995540> — [Ghost]({control_panel.jump_url}) the voice channel\n"
                               f"<:reveal:1361854891554766868> — [Reveal]({control_panel.jump_url}) the voice channel\n"
                               f"<:claim:1361852362523672846> — [Claim]({control_panel.jump_url}) the voice channel\n"
                               f"<:disconnect:1361853954698383513> — [Disconnect]({control_panel.jump_url}) a member\n"
                               f"<:activity:1361848643962929222> — [Start]({control_panel.jump_url}) an activity\n"
                               f"<:information:1361854914707587092> — [View]({control_panel.jump_url}) channel information\n"
                               f"<:Increase:1361849878153527378> — [Increase]({control_panel.jump_url}) the user limit\n"
                               f"<:decrease:1361850052963733616> — [Decrease]({control_panel.jump_url}) the user limit",
                    color=self.cog.config['embed_colors']['default']
                )
                interface_embed.set_author(name="VoiceMaster Interface")
                
                await control_panel.send(embed=interface_embed, view=VoiceMasterButtons(self.cog))

                # Create success embed
                success_embed = discord.Embed(
                    title="VoiceMaster Setup Complete",
                    description=f"Successfully created VoiceMaster channels!\n\nInterface: {control_panel.mention}\nJoin Channel: {join_channel.mention}",
                    color=self.cog.config['embed_colors']['success']
                )
                
                await interaction.response.edit_message(embed=success_embed, view=None)

            @discord.ui.button(label="No", style=discord.ButtonStyle.red)
            async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()

        # Send the embed with buttons
        await ctx.send(embed=embed, view=SetupButtons(self))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if user joined the "Join 2 Create" channel
        guild_id = str(member.guild.id)
        if guild_id in self.voice_channels and after.channel and str(after.channel.id) == self.voice_channels[guild_id]["join_channel_id"]:
            # Create new voice channel
            category = after.channel.category
            permissions = {
                member: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,
                    stream=True,
                    use_voice_activation=True,
                    use_soundboard=True,
                    priority_speaker=True
                )
            }
            
            new_channel = await category.create_voice_channel(
                f"{member.display_name}'s channel",
                overwrites=permissions
            )
            
            # Move user to new channel
            await member.move_to(new_channel)
            
            # Store channel info
            self.temp_channels[new_channel.id] = member.id

        # Check if user left a temporary channel
        if before.channel and before.channel.id in self.temp_channels:
            # If channel is empty or only the creator left and was alone
            if not before.channel.members or (
                len(before.channel.members) == 0 and 
                member.id == self.temp_channels[before.channel.id]
            ):
                await before.channel.delete()
                del self.temp_channels[before.channel.id]

    async def cog_load(self):
        """This is called when the cog is loaded"""
        self.bot.add_view(VoiceMasterButtons(self))  # Add the view when the cog loads

async def setup(bot):
    await bot.add_cog(VoiceMaster(bot)) 