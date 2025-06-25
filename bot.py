import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import asyncio
import wavelink
import subprocess
import sys
import time
import signal
import threading
import shutil

# Load environment variables from .env file
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX', '!')  # Default prefix is '!' if not specified

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Set up the bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.members = True  # Enable member intents

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.config = config
        self.lavalink_process = None
        self.lavalink_available = True  # Always available with external server

    def check_java_available(self):
        """Check if Java is available in the system"""
        return shutil.which('java') is not None

    def start_lavalink(self):
        """Start Lavalink server as a subprocess (only if local)"""
        try:
            # Check if Java is available
            if not self.check_java_available():
                print("Java is not available in this environment.")
                print("Using external Lavalink server for music functionality.")
                return True  # Return True because we'll use external server
            
            lavalink_path = os.path.join(os.getcwd(), 'Lavalink', 'Lavalink.jar')
            if not os.path.exists(lavalink_path):
                print(f"Lavalink.jar not found locally.")
                print("Using external Lavalink server for music functionality.")
                return True  # Return True because we'll use external server
            
            print("Starting local Lavalink server...")
            self.lavalink_process = subprocess.Popen(
                ['java', '-jar', 'Lavalink.jar'],
                cwd=os.path.join(os.getcwd(), 'Lavalink'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait a bit for Lavalink to start
            time.sleep(3)
            
            if self.lavalink_process.poll() is None:
                print("Local Lavalink server started successfully!")
                return True
            else:
                print("Failed to start local Lavalink server!")
                print("Using external Lavalink server for music functionality.")
                return True  # Return True because we'll use external server
        except Exception as e:
            print(f"Error starting local Lavalink: {e}")
            print("Using external Lavalink server for music functionality.")
            return True  # Return True because we'll use external server

    def stop_lavalink(self):
        """Stop Lavalink server"""
        if self.lavalink_process:
            try:
                self.lavalink_process.terminate()
                self.lavalink_process.wait(timeout=5)
                print("Local Lavalink server stopped.")
            except subprocess.TimeoutExpired:
                self.lavalink_process.kill()
                print("Local Lavalink server force killed.")
            except Exception as e:
                print(f"Error stopping Lavalink: {e}")

    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        # Start Lavalink in a separate thread (if local)
        def start_lavalink_thread():
            self.start_lavalink()
        
        thread = threading.Thread(target=start_lavalink_thread)
        thread.daemon = True
        thread.start()
        
        # Wait for Lavalink to start
        await asyncio.sleep(5)

bot = Bot()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is connected to {len(bot.guilds)} guilds')
    
    # Set up wavelink with external Lavalink server
    try:
        print("Connecting to Lavalink server...")
        
        # Try multiple Lavalink servers as fallbacks
        lavalink_servers = [
            {
                'uri': 'lavalink.devamop.in:443',
                'password': 'DevamOP'
            },
            {
                'uri': 'lavalink.oops.wtf:443',
                'password': 'www.freelavalink.ga'
            },
            {
                'uri': 'lavalink.lexnet.cc:443',
                'password': 'lexn3tl@val!nk'
            }
        ]
        
        connected = False
        for server in lavalink_servers:
            try:
                print(f"Trying to connect to {server['uri']}...")
                node = wavelink.Node(
                    uri=server['uri'],
                    password=server['password']
                )
                
                # Try to connect with shorter timeout
                await asyncio.wait_for(
                    wavelink.Pool.connect(nodes=[node], client=bot),
                    timeout=10.0
                )
                print(f"✅ Connected to Lavalink server: {server['uri']}")
                print("✅ Music functionality is available!")
                bot.lavalink_available = True
                connected = True
                break
                
            except asyncio.TimeoutError:
                print(f"❌ Timeout connecting to {server['uri']}")
                continue
            except Exception as e:
                print(f"❌ Failed to connect to {server['uri']}: {e}")
                continue
        
        if not connected:
            print("❌ All Lavalink servers failed to connect")
            print("❌ Music commands will not be available.")
            bot.lavalink_available = False
        
    except Exception as e:
        print(f"❌ Failed to connect to any Lavalink server: {e}")
        print("❌ Music commands will not be available.")
        bot.lavalink_available = False
    
    # Load the cogs
    print("Loading commands...")
    await bot.load_extension('commands.info.ping')
    await bot.load_extension('commands.info.avatar')
    await bot.load_extension('commands.info.banner')
    await bot.load_extension('commands.info.info')
    await bot.load_extension('commands.info.timezone')
    await bot.load_extension('commands.moderation.ban')
    await bot.load_extension('commands.moderation.unban')
    await bot.load_extension('commands.moderation.softban')
    await bot.load_extension('commands.moderation.hardban')
    await bot.load_extension('commands.moderation.kick')
    await bot.load_extension('commands.moderation.timeout')
    await bot.load_extension('commands.moderation.untimeout')
    await bot.load_extension('commands.moderation.nuke')
    await bot.load_extension('commands.user.afk')
    await bot.load_extension('commands.voicemaster.voicemaster')
    await bot.load_extension('commands.server.welcome')
    await bot.load_extension('commands.server.goodbye')
    await bot.load_extension('commands.embed.embed')
    
    # Load music commands
    if bot.lavalink_available:
        print("Loading music commands...")
        await bot.load_extension('commands.music.play')
        await bot.load_extension('commands.music.pause')
        await bot.load_extension('commands.music.resume')
        await bot.load_extension('commands.music.skip')
        await bot.load_extension('commands.music.stop')
        await bot.load_extension('commands.music.queue')
        await bot.load_extension('commands.music.nowplaying')
        await bot.load_extension('commands.music.volume')
        await bot.load_extension('commands.music.shuffle')
        await bot.load_extension('commands.music.remove')
        await bot.load_extension('commands.music.loop')
        await bot.load_extension('commands.music.clear')
        print("✅ Music commands loaded!")
    else:
        print("❌ Skipping music commands (Lavalink connection failed)")
    
    print("✅ Bot is ready!")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down bot...")
    bot.stop_lavalink()
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file")
        print("Please create a .env file with your Discord bot token:")
        print("DISCORD_TOKEN=your_bot_token_here")
        print("DISCORD_PREFIX=!")
    else:
        try:
            bot.run(TOKEN)
        except KeyboardInterrupt:
            print("\nShutting down bot...")
            bot.stop_lavalink()
        except Exception as e:
            print(f"Error running bot: {e}")
            bot.stop_lavalink()
