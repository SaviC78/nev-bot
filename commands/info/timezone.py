import discord
from discord.ext import commands
import json
from datetime import datetime
import pytz
import os

class Timezone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        # Load user timezones
        self.timezones = self.load_timezones()
        # Load timezone mappings
        self.timezone_maps = self.load_timezone_mappings()

    def load_timezones(self):
        if not os.path.exists('data/user'):
            os.makedirs('data/user')
        if not os.path.exists('data/user/timezones.json'):
            with open('data/user/timezones.json', 'w') as f:
                json.dump({}, f)
            return {}
        try:
            with open('data/user/timezones.json', 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            # If the file is empty or invalid, create a new empty dict
            with open('data/user/timezones.json', 'w') as f:
                json.dump({}, f)
            return {}

    def load_timezone_mappings(self):
        mappings = {}
        # Load all mapping files from the timezone_mappings directory
        mapping_dir = 'data/timezone_mappings'
        for filename in os.listdir(mapping_dir):
            if filename.endswith('.json'):
                with open(os.path.join(mapping_dir, filename), 'r') as f:
                    mappings.update(json.load(f))
        return mappings

    def save_timezones(self):
        with open('data/user/timezones.json', 'w') as f:
            json.dump(self.timezones, f)

    def get_timezone_from_location(self, location):
        location = location.lower().strip()
        
        # First check if it's a direct timezone name
        try:
            pytz.timezone(location)
            return location
        except pytz.exceptions.UnknownTimeZoneError:
            pass

        # Check all categories in the timezone mappings
        for category in self.timezone_maps:
            if location in self.timezone_maps[category]:
                return self.timezone_maps[category][location]
        
        # If not found in mappings, try to find a matching timezone
        for tz in pytz.common_timezones:
            if location in tz.lower():
                return tz
        return None

    @commands.command(name="timezone", aliases=["tz", "time"])
    async def timezone(self, ctx, *, member: discord.Member = None):
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author

        # Check if user has timezone set
        if str(member.id) not in self.timezones:
            if member == ctx.author:
                # Self-check with buttons
                embed = discord.Embed(
                    title="⏰ Timezone Not Set",
                    description=f"{member.mention}, you haven't set your timezone yet. Would you like to set it now?\n\nYou can use:\n- Country names (e.g., 'Japan', 'France')\n- City names (e.g., 'Tokyo', 'London')\n- US States (e.g., 'California', 'New York')\n- Timezone abbreviations (e.g., 'EST', 'GMT')\n- Regions (e.g., 'East Coast', 'Western Europe')\n- Full timezone names (e.g., 'America/New_York', 'Europe/London')",
                    color=self.config['embed_colors']['warning']
                )
                view = TimezoneSetupView(ctx, member, self)
                await ctx.send(embed=embed, view=view)
            else:
                # Check for other user
                embed = discord.Embed(
                    description=f"⏰ {member.mention} hasn't set their timezone yet.",
                    color=self.config['embed_colors']['warning']
                )
                await ctx.send(embed=embed)
        else:
            # Show current time
            tz = pytz.timezone(self.timezones[str(member.id)])
            current_time = datetime.now(tz)
            time_str = current_time.strftime("%B %d, %I:%M %p")
            
            embed = discord.Embed(
                description=f"⏰ {member.mention}'s current time is **{time_str}**",
                color=self.config['embed_colors']['default']
            )
            await ctx.send(embed=embed)

class TimezoneSetupView(discord.ui.View):
    def __init__(self, ctx, member, cog):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.member = member
        self.cog = cog

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"⏰ {self.member.mention}, please type your location",
            color=self.cog.config['embed_colors']['default']
        )
        await interaction.response.send_message(embed=embed)
        
        def check(m):
            return m.author == self.member and m.channel == self.ctx.channel

        try:
            msg = await self.cog.bot.wait_for('message', check=check, timeout=60)
            timezone = self.cog.get_timezone_from_location(msg.content)
            
            if timezone:
                self.cog.timezones[str(self.member.id)] = timezone
                self.cog.save_timezones()
                
                embed = discord.Embed(
                    description=f"⏰ Your timezone has been set to {timezone}",
                    color=self.cog.config['embed_colors']['success']
                )
                await msg.reply(embed=embed)
            else:
                embed = discord.Embed(
                    title="Invalid Location",
                    description="I couldn't find a matching timezone for that location. Please try again with a more specific location.",
                    color=self.cog.config['embed_colors']['warning']
                )
                await msg.reply(embed=embed)
        except TimeoutError:
            pass

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(Timezone(bot)) 