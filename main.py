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

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(script_dir, '.env'))
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

DB_FILE = "stats.db"

def initdb():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messaging_stats (
            guild_id INTEGER,
            user_id INTEGER,
            message_count INTEGER DEFAULT 0,
            PRIMARY KEY(guild_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_logs (
                guild_id INTEGER,
               user_id INTEGER,
               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_configs (
                   guild_id INTEGER PRIMARY KEY, 
                   is_indexed BOOLEAN DEFAULT 0
            )
''')
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    initdb()

    print("I'm online and syncing commands!")
    try: 
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO messaging_stats (guild_id, user_id, message_count)
        VALUES (?, ?,1)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET message_count = message_count + 1
    ''', (guild_id, user_id))


    cursor.execute('''
        INSERT INTO message_logs (guild_id, user_id)
        VALUES (?, ?)
    ''', (guild_id, user_id))
    
    conn.commit()
    conn.close()
    await bot.process_commands(message)


@bot.tree.command(name="setup", description="Manually trigger the database sync for this server")
@app_commands.describe(force="Force a re-scan even if server's already been scanned")
# @app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, force: bool = False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == 1 and not force:
        await interaction.response.send_message("**Server has already been scanned for past messages!** If you want to re-scan (this may take a long time and may double up the data) use the `/setup force:True` command.",
                                                ephemeral=True
                                                )
        return 

    view = ServerSetupView(interaction.guild.id)
    await interaction.response.send_message(
        "Click the button below to authorize the initial server scan!",
        view=view,
        ephemeral=True
    )


@bot.tree.command(name="wipe-server-data", description="Delete all stored message data for this server")
# @app_commands.checks.has_permissions(administrator=True)
async def wipe_server_data(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    view = WipeServerDataView(interaction.guild.id)
    await interaction.response.send_message(
        "This will permanently delete all stored data for this server. Are you sure?",
        view=view,
        ephemeral=True,
    )

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
        await interaction.followup.send("No messages have been sent in this server")
        return

    response = "## Top Chatters in the Last 100 Messages\n"
    for name, count in sorted_users[:5]:
        response += f"**{name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-hour", description="Tells you who has the most messages within the last hour on the server")
async def lasthourmsgs(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row [0] == 0:
        await interaction.response.send_message(
            "This server hasn't been scraped for message data yet. Please have the server owner run `/setup` to initialize the database.", 
            ephemeral=True
        )
        return

    await interaction.response.defer()
    
    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    time_limit = (now - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
   
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                    SELECT user_id, COUNT(*) as count
                    FROM message_logs 
                    WHERE guild_id = ? AND timestamp >= ?
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10 
    ''', (interaction.guild.id, time_limit))

    rows = cursor.fetchall()
    conn.close()

    

    if not rows: #if channel is empty
        await interaction.followup.send("No messages have been sent in this server in the last hour")
        return

    response = "## Top Chatters in the Last Hour\n" #if channel not empty
    for user_id, count in rows:
        member = interaction.guild.get_member(user_id)
        display_name = member.display_name if member else f"User ({user_id})"
        response += f"**{display_name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-day", description="Tells you who has the most messages within the last 24 hours on the server")
async def lastdaymsgs(interaction: discord.Interaction):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row [0] == 0:
        await interaction.response.send_message(
            "This server hasn't been scraped for message data yet. Please have the server owner run `/setup` to initialize the database.", 
            ephemeral=True
        )
        return

    await interaction.response.defer()

    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    time_limit = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                    SELECT user_id, COUNT(*) as count
                    FROM message_logs 
                    WHERE guild_id = ? AND timestamp >= ?
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10 
    ''', (interaction.guild.id, time_limit))

    rows = cursor.fetchall()
    conn.close()

    if not rows: #if channel is empty
        await interaction.followup.send("No messages have been sent in this server for the last 24 hours")
        return

    response = "## Top Chatters in the Last 24 hours\n" #if channel not empty
    for user_id, count in rows:
        member = interaction.guild.get_member(user_id)
        display_name = member.display_name if member else f"User ({user_id})"
        response += f"**{display_name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="last-week", description="Tells you who has the most messages within the last 7 days on the server")
async def lastweekmsgs(interaction: discord.Interaction):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row [0] == 0:
        await interaction.response.send_message(
            "This server hasn't been scraped for message data yet. Please have the server owner run `/setup` to initialize the database.", 
            ephemeral=True
        )
        return

    await interaction.response.defer()

    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    time_limit = (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                    SELECT user_id, COUNT(*) as count
                    FROM message_logs 
                    WHERE guild_id = ? AND timestamp >= ?
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10 
    ''', (interaction.guild.id, time_limit))

    rows = cursor.fetchall()
    conn.close()
    

    if not rows: #if channel is empty
        await interaction.followup.send("No messages have been sent in this server in the last 7 days")
        return

    response = "## Top Chatters in the Last 7 days\n" #if channel not empty
    for user_id, count in rows:
        member = interaction.guild.get_member(user_id)
        display_name = member.display_name if member else f"User ({user_id})"
        response += f"**{display_name}** : {count} messages\n"
        
    await interaction.followup.send(response)

@bot.tree.command(name="last-month", description="Tells you who has the most messages within the last 30 days on the server")
async def lastmonthmsgs(interaction: discord.Interaction):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row [0] == 0:
        await interaction.response.send_message(
            "This server hasn't been scraped for message data yet. Please have the server owner run `/setup` to initialize the database.", 
            ephemeral=True
        )
        return

    await interaction.response.defer()

    now = datetime.datetime.now(datetime.timezone.utc) #finds current time
    time_limit = (now - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                    SELECT user_id, COUNT(*) as count
                    FROM message_logs 
                    WHERE guild_id = ? AND timestamp >= ?
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10 
    ''', (interaction.guild.id, time_limit))

    rows = cursor.fetchall()
    conn.close()
    

    if not rows: #if channel is empty
        await interaction.followup.send("No messages have been sent in this server in the last 30 days")
        return

    response = "## Top Chatters in the Last 30 days\n" #if channel not empty
    for user_id, count in rows:
        member = interaction.guild.get_member(user_id)
        display_name = member.display_name if member else f"User ({user_id})"
        response += f"**{display_name}** : {count} messages\n"
        
    await interaction.followup.send(response)


@bot.tree.command(name="all-time", description="Tells you who has the most messages in a server")
async def alltime(interaction: discord.Interaction):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_indexed FROM  guild_configs WHERE guild_id = ?", (interaction.guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row [0] == 0:
        await interaction.response.send_message(
            "This server hasn't been scraped for message data yet. Please have the server owner run `/setup` to initialize the database.", 
            ephemeral=True
        )
        return

    await interaction.response.defer()

    guild_id = interaction.guild.id

    conn = sqlite3.connect(DB_FILE)
    cursor =  conn.cursor()
    cursor.execute('''SELECT user_id, message_count 
                   FROM messaging_stats 
                   WHERE guild_id = ? 
                   ORDER BY message_count DESC 
                   LIMIT 10
                   ''', (guild_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await interaction.followup.send("No message data has been saved yet!")
        return
    
    response = "## Biggest YAPPERS in the Server All Time\n"
    for user_id, count in rows:
        member = interaction.guild.get_member(user_id)
        display_name = member.display_name if member else f"User ({user_id})"
        response += f"**{display_name}** : {count} messages \n"

    await interaction.followup.send(response)






class ServerSetupView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
    @discord.ui.button(label="Confirm and Sync Server Data", style= discord.ButtonStyle.green)
    async def confirm_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        await interaction.edit_original_response(content="**Scan started!** I am scanning all the historical messages from your server. I'll let you know when I'm done!", view=None)
        bot_instance= interaction.client
        guild = bot_instance.get_guild(self.guild_id)
        
        if not guild:
            await interaction.followup.send("**ERROR.** I couldn't find that server. Did I get kicked already?!?!")
            return

        server_msg_count = {}
        historical_logs = []
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).read_message_history:
                try:
                    async for message in channel.history(limit=None):
                        if not message.author.bot:
                            user_id = message.author.id
                            server_msg_count[user_id] = server_msg_count.get(user_id, 0) + 1

                            msg_time = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            historical_logs.append((self.guild_id, user_id, msg_time))
                
                except Exception as e:
                    print(f"Skipping channel {channel.name} due to an unexpected error: {e}")

        if server_msg_count:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            if historical_logs:
                cursor.executemany('''
                        INSERT INTO message_logs (guild_id, user_id, timestamp)
                        VALUES (?,?,?)
            ''', historical_logs)

            for user_id, count in server_msg_count.items():
                cursor.execute('''
                                INSERT INTO messaging_stats (guild_id, user_id, message_count)
                                VALUES (?, ?, ?)
                                ON CONFLICT (guild_id, user_id) DO UPDATE SET message_count = ?
                                ''', (self.guild_id, user_id, count, count))
                
            cursor.execute("INSERT OR REPLACE INTO guild_configs (guild_id, is_indexed) VALUES (?, 1)", (self.guild_id,))
            conn.commit()
            conn.close()
            print(f"Database updated for guild {self.guild_id}. Row inserted/updated.")

                
            
        await interaction.followup.send(f"**SUCCESS!!!** Setup complete for **{guild.name}**. The /all-time leaderboard database has now been initialized!")


class WipeServerDataView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="Yes, Wipe Everything", style=discord.ButtonStyle.danger)
    async def confirm_wipe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM messaging_stats WHERE guild_id = ?", (self.guild_id,))
        cursor.execute("DELETE FROM message_logs WHERE guild_id = ?", (self.guild_id,))
        cursor.execute("UPDATE guild_configs SET is_indexed = 0 WHERE guild_id = ?", (self.guild_id,))

        conn.commit()
        conn.close()

        await interaction.edit_original_response(
            content="Server data has been wiped for this server.",
            view=None,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_wipe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Operation cancelled.",
            view=None,
        )

                                            

@bot.event
async def on_guild_join(guild: discord.Guild):
    print (f"Joined a new server: {guild.name}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO guild_configs (guild_id, is_indexed) VALUES (?, 0)", (guild.id,))
    conn.commit()
    conn.close()

    if guild.owner:
        try:
            view = ServerSetupView(guild.id)
            await guild.owner.send(
                f"Hello! I have just joined your server: **{guild.name}**.\n\n"
                "To initiliaze the /all-time command, I need to scan your text channels and index all the message counts into my local database.\n"
                "Click the button below to authorize and give me permission to do this setup synchronization!", 
                view = view
            )
        except Exception as e:
            print(f"Could not send a setup DM to the owner of **{guild.name}**: {e}")
    


bot.run(token, log_handler=handler, log_level=logging.DEBUG) #any logs needed for debugging will be logged in discord.log file