# Top Chatter Bot 

Welcome to **Top Chatter**. Basically, I wanted to figure out who the biggest yappers in my Discord server were, so I built this. It tracks message counts and ranks everyone so you can finally prove who needs to go outside and touch grass.

I started this project to learn Python and `discord.py`, and it's honestly grown a lot. We went from scraping the API to a full local database setup. 

## Features

* **Time-Based Leaderboards:** See who is chatting the most with `/last-100-messages`, `/last-hour`, `/last-day`, and `/last-week`.
* **All-Time Rankings:** Use `/all-time` to see the top 10 biggest yappers in the server's history. 
* **Zero Lag:** Instead of scraping Discord's API every single time a command is run, the bot logs messages in real-time to a local SQLite database (`stats.db`). It's fast and doesn't get rate-limited.
* **Name Change resistant:** Tracks stats using Discord `user_id` instead of display names. If someone changes their nickname to try and hide from the leaderboard, the bot still catches them. Huge W.
* **Auto Syncable:** When the bot joins a new server, it sends the owner a DM with a setup button. Click it, and it automatically scans the server's history to build the initial database. 

## Tech Used:
* **Python 3** 
* **discord.py** (for the bot framework)
* **SQLite3** (for the local database)

## Invite the Bot to Your Server

I will be hosting this bot 24/7 so you don't have to worry about running any code. You can add it to your own server using the invite link:
https://discord.com/oauth2/authorize?client_id=1514369908085887037&permissions=8&integration_type=0&scope=bot+applications.commands


Or join this test server with the bot to run the commands:
https://discord.gg/g87c4mmTg

