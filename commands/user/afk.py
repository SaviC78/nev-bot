import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        # Load AFK data
        self.afk_file = 'data/user/afk.json'
        if not os.path.exists('data/user'):
            os.makedirs('data/user')
        if not os.path.exists(self.afk_file):
            with open(self.afk_file, 'w') as f:
                json.dump({"users": {}}, f)
        self.load_afk_data()

    def load_afk_data(self):
        with open(self.afk_file, 'r') as f:
            self.afk_data = json.load(f)

    def save_afk_data(self):
        with open(self.afk_file, 'w') as f:
            json.dump(self.afk_data, f, indent=4)

    def format_duration(self, seconds):
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif seconds < 2592000:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            months = seconds // 2592000
            return f"{months} month{'s' if months != 1 else ''}"

    async def get_pings_text(self, pings, page):
        pings_per_page = 5
        start_idx = (page - 1) * pings_per_page
        end_idx = start_idx + pings_per_page
        current_pings = pings[start_idx:end_idx]
        
        pings_text = ""
        for ping in current_pings:
            try:
                channel = self.bot.get_channel(int(ping['message_url'].split('/')[-2]))
                message = await channel.fetch_message(int(ping['message_url'].split('/')[-1]))
                content = message.content
                if len(content) > 50:
                    content = content[:50] + "..."
                pings_text += f"{message.author.mention}: {content} [Click to jump to message]({ping['message_url']})\n"
            except:
                pings_text += f"[Click to jump to message]({ping['message_url']})\n"
        return pings_text

    @commands.command(name="afk")
    async def afk(self, ctx, *, status: str = "AFK"):
        user_id = str(ctx.author.id)
        
        # Create AFK embed
        embed = discord.Embed(
            description=f"{ctx.author.mention}: You're now AFK with the status: **{status}**",
            color=self.config['embed_colors']['default']
        )
        await ctx.send(embed=embed)

        # Save AFK data
        self.afk_data["users"][user_id] = {
            "status": status,
            "time": datetime.utcnow().timestamp(),
            "pings": []
        }
        self.save_afk_data()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        
        # Check for mentions first
        for mention in message.mentions:
            mention_id = str(mention.id)
            if mention_id in self.afk_data["users"]:
                afk_data = self.afk_data["users"][mention_id]
                
                # Create AFK notification embed
                embed = discord.Embed(
                    description=f"{mention.mention}: Is AFK: **{afk_data['status']}** - {self.format_duration(int(datetime.utcnow().timestamp() - afk_data['time']))} ago",
                    color=self.config['embed_colors']['default']
                )
                await message.reply(embed=embed)

                # Add ping to user's AFK data
                afk_data["pings"].append({
                    "message_url": message.jump_url,
                    "time": datetime.utcnow().timestamp()
                })
                self.save_afk_data()

        # Then check if user is no longer AFK
        if user_id in self.afk_data.get("users", {}):  # Safely check if user exists in AFK data
            # Don't remove AFK status for commands
            if message.content.startswith(self.bot.command_prefix):
                return
                
            afk_data = self.afk_data["users"][user_id]
            time_away = int(datetime.utcnow().timestamp() - afk_data["time"])
            
            # Remove user from AFK list first to prevent duplicate messages
            try:
                del self.afk_data["users"][user_id]
                self.save_afk_data()
            except KeyError:
                return  # User was already removed from AFK list
            
            # Create welcome back embed
            embed = discord.Embed(
                description=f"{message.author.mention}: Welcome back, you were away for **{self.format_duration(time_away)}**",
                color=self.config['embed_colors']['default']
            )

            # Add pings field if there are any
            if afk_data["pings"]:
                total_pages = (len(afk_data["pings"]) + 4) // 5  # Ceiling division
                current_page = 1
                
                pings_text = await self.get_pings_text(afk_data["pings"], current_page)
                embed.add_field(name=f"Pings: {len(afk_data['pings'])}", value=pings_text, inline=False)
                if total_pages > 1:
                    embed.set_footer(text=f"Page {current_page}/{total_pages}")

                # Send welcome back message with pagination
                welcome_msg = await message.reply(embed=embed)
                
                if total_pages > 1:
                    await welcome_msg.add_reaction("⬅️")
                    await welcome_msg.add_reaction("➡️")

                    def check(reaction, user):
                        return user == message.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == welcome_msg.id

                    while True:
                        try:
                            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                            
                            if str(reaction.emoji) == "➡️" and current_page < total_pages:
                                current_page += 1
                            elif str(reaction.emoji) == "⬅️" and current_page > 1:
                                current_page -= 1
                            
                            pings_text = await self.get_pings_text(afk_data["pings"], current_page)
                            embed.set_field_at(0, name=f"Pings: {len(afk_data['pings'])}", value=pings_text)
                            embed.set_footer(text=f"Page {current_page}/{total_pages}")
                            await welcome_msg.edit(embed=embed)
                            await welcome_msg.remove_reaction(reaction, user)
                            
                        except asyncio.TimeoutError:
                            break

            else:
                # Send welcome back message without pagination
                await message.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message_reply(self, message):
        if message.author.bot:
            return

        # Check if the replied-to user is AFK
        if message.reference and message.reference.resolved:
            replied_user = message.reference.resolved.author
            if replied_user.bot:
                return

            replied_id = str(replied_user.id)
            if replied_id in self.afk_data["users"]:
                afk_data = self.afk_data["users"][replied_id]
                
                # Create AFK notification embed
                embed = discord.Embed(
                    description=f"{replied_user.mention}: Is AFK: **{afk_data['status']}** - {self.format_duration(int(datetime.utcnow().timestamp() - afk_data['time']))} ago",
                    color=self.config['embed_colors']['default']
                )
                await message.reply(embed=embed)

                # Add ping to user's AFK data
                afk_data["pings"].append({
                    "message_url": message.jump_url,
                    "time": datetime.utcnow().timestamp()
                })
                self.save_afk_data()

async def setup(bot):
    await bot.add_cog(AFK(bot)) 