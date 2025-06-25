# NEV Discord Bot

A Discord bot with music capabilities, moderation tools, and various utility commands.

## Features

- 🎵 **Music System**: Full music playback with Lavalink (automatically managed)
- 🛡️ **Moderation**: Ban, kick, timeout, and other moderation commands
- 👥 **User Management**: Welcome/goodbye messages, AFK system
- 🎭 **Roleplay**: Voice master and other roleplay features
- 📊 **Info Commands**: User info, avatar, banner, ping, timezone
- 🎨 **Embed System**: Custom embed creation

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Java 11 or higher (for Lavalink)
- Discord Bot Token

### 2. Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory with:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_PREFIX=!
   ```

### 3. Running the Bot

**Simply run the bot and it will automatically start everything:**
```bash
python bot.py
```

The bot will:
1. Automatically start the Lavalink server
2. Connect to Discord
3. Load all commands including music functionality
4. Handle graceful shutdown when you stop the bot

## Music Commands

- `!play <song>` - Play a song or add to queue
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` - Skip to the next song
- `!stop` - Stop playing and clear queue
- `!queue` - Show the current queue
- `!nowplaying` - Show currently playing song
- `!volume <1-100>` - Set volume
- `!shuffle` - Shuffle the queue
- `!remove <position>` - Remove a song from queue
- `!loop` - Toggle loop mode
- `!clear` - Clear the queue

## Configuration

### Lavalink Configuration
The Lavalink server is configured in `Lavalink/application.yml`:
- Port: 2333
- Password: "youshallnotpass"
- Sources: YouTube, Bandcamp, SoundCloud, Twitch, Vimeo, HTTP

### Bot Configuration
Bot settings are in `config.json`:
- Embed colors for different message types
- Default prefix (can be overridden by DISCORD_PREFIX env var)

## File Structure

```
NEV/
├── bot.py                 # Main bot file (starts everything)
├── requirements.txt       # Python dependencies
├── config.json           # Bot configuration
├── .env                  # Environment variables (create this)
├── Lavalink/             # Lavalink server files
│   ├── Lavalink.jar      # Lavalink server
│   └── application.yml   # Lavalink configuration
├── commands/             # Bot commands organized by category
│   ├── music/           # Music commands
│   ├── moderation/      # Moderation commands
│   ├── info/            # Information commands
│   └── ...
├── data/                # Data storage
└── variables/           # Variable replacement system
```

## Troubleshooting

1. **Bot won't start:**
   - Make sure Java 11+ is installed and in your PATH
   - Check that you have a `.env` file with your Discord token
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **Music commands not working:**
   - Check that Java is installed: `java -version`
   - Look for Lavalink startup messages in the console
   - The bot will continue without music if Lavalink fails to start

3. **Missing dependencies:**
   - Run `pip install -r requirements.txt`
   - Make sure you're using Python 3.8+

## Support

For issues or questions, check the command implementations in the `commands/` directory or refer to the Discord.py and Wavelink documentation. 