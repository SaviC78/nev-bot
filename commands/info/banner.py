import discord
from discord.ext import commands
import json
from datetime import datetime

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    @commands.command(name="banner")
    async def banner(self, ctx, *, member: discord.Member = None):
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author

        # Fetch user to get global banner
        user = await self.bot.fetch_user(member.id)

        # Create the embed
        embed = discord.Embed(
            title=f"{member.name}'s Global Banner",
            color=self.config['embed_colors']['default']
        )

        if user.banner:
            embed.set_image(url=user.banner.url)
        else:
            embed.description = f"{member.name} doesn't have a banner set."

        embed.set_footer(text=f"Today at {datetime.utcnow().strftime('%I:%M %p')}")

        # Create the view with buttons
        view = BannerView(member, user, embed, self.config)

        # Send the message with the view
        await ctx.send(embed=embed, view=view)

class BannerView(discord.ui.View):
    def __init__(self, member, user, embed, config):
        super().__init__(timeout=None)
        self.member = member
        self.user = user
        self.embed = embed
        self.config = config
        self.is_global = True

    @discord.ui.button(label="Server Banner", style=discord.ButtonStyle.grey)
    async def switch_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_global:
            # Switch to server banner
            if self.member.guild_avatar:  # Using guild_avatar as a proxy for server banner
                self.embed.title = f"{self.member.name}'s Server Banner"
                self.embed.set_image(url=self.member.guild_avatar.url)
                self.embed.description = None
            else:
                self.embed.title = f"{self.member.name}'s Server Banner"
                if self.user.banner:
                    self.embed.set_image(url=self.user.banner.url)
                    self.embed.description = None
                else:
                    self.embed.description = f"{self.member.name} doesn't have a banner set."
                    self.embed.set_image(url=None)
            button.label = "Global Banner"
            self.is_global = False
        else:
            # Switch back to global banner
            self.embed.title = f"{self.member.name}'s Global Banner"
            if self.user.banner:
                self.embed.set_image(url=self.user.banner.url)
                self.embed.description = None
            else:
                self.embed.description = f"{self.member.name} doesn't have a banner set."
                self.embed.set_image(url=None)
            button.label = "Server Banner"
            self.is_global = True

        await interaction.response.edit_message(embed=self.embed, view=self)

async def setup(bot):
    await bot.add_cog(Banner(bot)) 