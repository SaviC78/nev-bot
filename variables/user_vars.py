import discord

def get_user_vars(user):
    """Get all user-related variables"""
    return {
        "{user.name}": user.name,
        "{user.id}": str(user.id),
        "{user.mention}": user.mention,
        "{user.avatar}": str(user.display_avatar.url) if user.display_avatar else str(user.default_avatar.url),
        "{user.created_at}": discord.utils.format_dt(user.created_at, style="f"),
        "{user.created_at_timestamp}": str(int(user.created_at.timestamp())),
        "{user.bot}": "Yes" if user.bot else "No",
        "{user.system}": "Yes" if user.system else "No",
        "{user.public_flags}": ", ".join([flag.name for flag in user.public_flags.all()]) if user.public_flags else "None",
        "{user.accent_color}": str(user.accent_color) if user.accent_color else "None",
        "{user.banner}": str(user.banner.url) if user.banner else "None",
        "{user.display_name}": user.display_name,
        "{user.global_name}": user.global_name if user.global_name else "None"
    } 