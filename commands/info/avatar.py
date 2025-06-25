import discord
from discord.ext import commands
import json
from datetime import datetime

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="avatar", aliases=["av"])
    async def avatar(self, ctx, *, user: discord.Member = None):
        # If no user is specified, use the command author
        if user is None:
            user = ctx.author

        # Create the embed with global avatar
        embed = discord.Embed(
            title=f"{user.name}'s Global Avatar",
            color=self.config['embed_colors']['default']
        )
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(text=f"Today at {datetime.utcnow().strftime('%I:%M %p')}")

        # Create the view with buttons
        view = AvatarView(user, embed, self.config)

        # Send the message with the view
        await ctx.send(embed=embed, view=view)

class AvatarView(discord.ui.View):
    def __init__(self, user, embed, config):
        super().__init__(timeout=None)
        self.user = user
        self.embed = embed
        self.config = config
        self.is_global = True

    @discord.ui.button(label="Server Avatar", style=discord.ButtonStyle.grey)
    async def switch_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_global:
            # Switch to server avatar
            if self.user.guild_avatar:
                self.embed.set_image(url=self.user.guild_avatar.url)
                self.embed.title = f"{self.user.name}'s Server Avatar"
            else:
                # If no server avatar, keep the global one
                self.embed.set_image(url=self.user.display_avatar.url)
                self.embed.title = f"{self.user.name}'s Server Avatar"
            button.label = "Global Avatar"
            self.is_global = False
        else:
            # Switch to global avatar
            self.embed.set_image(url=self.user.display_avatar.url)
            self.embed.title = f"{self.user.name}'s Global Avatar"
            button.label = "Server Avatar"
            self.is_global = True

        await interaction.response.edit_message(embed=self.embed, view=self)

async def setup(bot):
    await bot.add_cog(Avatar(bot)) 