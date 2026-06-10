import discord
from discord.ext import commands
from discord import app_commands #gives bot events and slash commands for users
from discord.ext import tasks #lets you run periodic jobs
import logging
from dotenv import load_dotenv #keep token out of source code
import os
import datetime #handles time
import sqlite3 #gives storiage without extra hosting cost
import asyncio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

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
    print("I'm ready to get ready in {bot.user.name} ayyyyyyyy tough tough")

bot.run(token, log_handler=handler, log_level=logging.DEBUG) #any logs needed for debugging will be logged in discord.log file
