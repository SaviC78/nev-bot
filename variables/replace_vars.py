import discord
from variables.user_vars import get_user_vars
from variables.guild_vars import get_guild_vars
from variables.channel_vars import get_channel_vars

def replace_variables(text, ctx):
    """Replace variables in text with their actual values"""
    if not text:
        return text
        
    # Handle both Member objects and context objects
    if isinstance(ctx, discord.Member):
        # If ctx is a Member object, use it directly
        user = ctx
        guild = ctx.guild
        channel = None  # No channel for Member objects
    else:
        # If ctx is a context object, get the appropriate values
        guild = ctx.guild if isinstance(ctx, discord.ext.commands.Context) else ctx.guild
        user = ctx.author if isinstance(ctx, discord.ext.commands.Context) else ctx.user
        channel = ctx.channel if isinstance(ctx, discord.ext.commands.Context) else ctx.channel
    
    # Get all variables
    variables = {}
    variables.update(get_user_vars(user))
    variables.update(get_guild_vars(guild))
    if channel:  # Only add channel variables if we have a channel
        variables.update(get_channel_vars(channel))
    
    # Replace all variables, ensuring values are strings
    for var, value in variables.items():
        if value is None:
            text = text.replace(var, "None")
        else:
            text = text.replace(var, str(value))
    
    return text 