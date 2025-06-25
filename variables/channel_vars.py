import discord

def get_channel_vars(channel):
    """Get all channel-related variables"""
    return {
        "{channel.name}": channel.name,
        "{channel.id}": str(channel.id),
        "{channel.mention}": channel.mention,
        "{channel.created_at}": discord.utils.format_dt(channel.created_at, style="f"),
        "{channel.created_at_timestamp}": str(int(channel.created_at.timestamp())),
        "{channel.position}": str(channel.position),
        "{channel.type}": str(channel.type).replace("ChannelType.", ""),
        "{channel.category}": channel.category.name if channel.category else "None",
        "{channel.category_id}": str(channel.category_id) if channel.category_id else "None",
        "{channel.topic}": channel.topic if hasattr(channel, 'topic') and channel.topic else "None",
        "{channel.nsfw}": "Yes" if hasattr(channel, 'nsfw') and channel.nsfw else "No",
        "{channel.slowmode_delay}": str(channel.slowmode_delay) if hasattr(channel, 'slowmode_delay') else "None",
        "{channel.bitrate}": str(channel.bitrate) if hasattr(channel, 'bitrate') else "None",
        "{channel.user_limit}": str(channel.user_limit) if hasattr(channel, 'user_limit') else "None"
    } 