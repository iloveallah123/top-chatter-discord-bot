import os
import certifi
os.environ.setdefault('SSL_CERT_FILE', certifi.where())

import discord
from discord.ext import commands
from discord import app_commands #gives bot events and slash commands for users
from discord.ext import tasks #lets you run periodic jobs
import logging
from dotenv import load_dotenv #keep token out of source code
import datetime #handles time
import sqlite3 #gives storiage without extra hosting cost
import asyncio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if not token:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to your .env file.")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/' , intents = intents)

@bot.event
async def on_ready():
    print("I'm online and syncing commands!")
    try: 
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="test", description= "Test if the bot is working")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}, your command is working")


@bot.tree.command(name="last-100-messages", description="Tells you who has the most messages within the last 100 messages on the server")
async def msgs100(interaction: discord.Interaction):
    msg_count = {} #creates dictionary
    await interaction.response.defer()
    async for message in interaction.channel.history(limit=100):
        user_id = message.author.display_name
        if user_id in msg_count: 
            msg_count[user_id] = msg_count[user_id] + 1
        else:
            msg_count[user_id] = 1
    sorted_users = sorted(msg_count.items(), key=lambda item: item[1], reverse=True)

    if not sorted_users:
        await interaction.followup.send("No messages have been sent in this channel")
        return

    response = "## Top Chatters in the Last 100 Messages\n"
    for name, count in sorted_users[:5]:
        response += f"**{name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-hour", description="Tells you who has the most messages within the last hour on the server")
async def lasthourmsgs(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    one_hour_ago = now - datetime.timedelta(hours=1) #calculates time exactly 1 hour ago
    msg_count = {} #sets up message dictionary
    await interaction.response.defer()
    async for message in interaction.channel.history(after=one_hour_ago, limit=None):
        user_id = message.author.display_name
        if user_id in msg_count: 
            msg_count[user_id] = msg_count[user_id] + 1
        else:
            msg_count[user_id] = 1
    sorted_users = sorted(msg_count.items(), key=lambda item: item[1], reverse=True)

    if not sorted_users: #if channel is empty
        await interaction.followup.send("No messages have been sent in this channel")
        return

    response = "## Top Chatters in the Last Hour\n" #if channel not empty
    for name, count in sorted_users[:5]:
        response += f"**{name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-day", description="Tells you who has the most messages within the last 24 hours on the server")
async def lastdaymsgs(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    one_day_ago = now - datetime.timedelta(days=1) #calculates time exactly 1 day ago
    msg_count = {} #sets up message dictionary
    await interaction.response.defer()
    async for message in interaction.channel.history(after=one_day_ago, limit=None):
        user_id = message.author.display_name
        if user_id in msg_count: 
            msg_count[user_id] = msg_count[user_id] + 1
        else:
            msg_count[user_id] = 1
    sorted_users = sorted(msg_count.items(), key=lambda item: item[1], reverse=True)

    if not sorted_users: #if channel is empty
        await interaction.followup.send("No messages have been sent in this channel")
        return

    response = "## Top Chatters in the Last 24 hours\n" #if channel not empty
    for name, count in sorted_users[:10]:
        response += f"**{name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-week", description="Tells you who has the most messages within the last 7 days on the server")
async def lastweekmsgs(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    one_week_ago = now - datetime.timedelta(days=7) #calculates time exactly 7 day ago
    msg_count = {} #sets up message dictionary
    await interaction.response.defer()
    async for message in interaction.channel.history(after=one_week_ago, limit=None):
        user_id = message.author.display_name
        if user_id in msg_count: 
            msg_count[user_id] = msg_count[user_id] + 1
        else:
            msg_count[user_id] = 1
    sorted_users = sorted(msg_count.items(), key=lambda item: item[1], reverse=True)

    if not sorted_users: #if channel is empty
        await interaction.followup.send("No messages have been sent in this channel")
        return

    response = "## Top Chatters in the Last 7 days\n" #if channel not empty
    for name, count in sorted_users[:10]:
        response += f"**{name}** : {count} messages\n"
        
    await interaction.followup.send(response)


class AllTimeConfirmView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction

    @discord.ui.button(label="Confirm & Run", style=discord.ButtonStyle.danger)
    async def confirm_and_run(self, interaction: discord.Interaction, button: discord.ui.Button):
        # We defer the button click interaction itself so it doesn't time out
        await interaction.response.defer()

        await self.interaction.edit_original_response(content="⏳ **Processing...** I am scanning the entire channel history. This will take a moment...", view=None)
        
        channel = self.interaction.channel
        msg_count = {}

        async for message in channel.history(limit=None):
            user_id = message.author.display_name
            if user_id in msg_count:
                msg_count[user_id] = msg_count[user_id] + 1
            else:
                msg_count[user_id] = 1

        sorted_users = sorted(msg_count.items(), key=lambda item: item[1], reverse=True)

        if not sorted_users:
            await self.interaction.followup.send("No messages have been sent in this channel")
            return

        response = "## Top Chatters in the server\n"
        for name, count in sorted_users[:10]:
            response += f"**{name}** : {count} messages\n"

        # Correctly responding as a follow-up to the original slash command
        await self.interaction.followup.send(response)


@bot.tree.command(name="all-time", description="Tells you who has the most messages in a server")
async def alltime(interaction: discord.Interaction):
    view = AllTimeConfirmView(interaction)
    await interaction.response.send_message(
        "⚠️ **WARNING:** This command can take a long time or crash the bot. Confirm only if you want to run it.",
        view=view,
    )

bot.run(token, log_handler=handler, log_level=logging.DEBUG) #any logs needed for debugging will be logged in discord.log file