# Top Chatter Bot 

I talk a lot... Especially in group chats with my friends on discord. We often use the discord search feature to see who has the most messages, but this is a manual process and requires you to look through every user and compare to see who has more messages. I wanted to solve this issue and learn how to make discord bots using Python and discord.py

## Features

* **Message Commands:** See who has the most messages using commands. There are many different commands to see who's talked the most throughout different time periods.
  Here are all of them:
    - `/last-100-messages`
    -  `/last-hour`
    -  `/last-day` 
    -  `/last-week`
    -  `/last-month`
    -  `/all-time`

* **Setup Features:** When the bot is added to a server, there are a few ways you can set it up to get it's database initiliazed with any and all previous messaging data.
  - When it's added to the server, it automatically dm's the server owner with a button they can press to start the initialization process
  - If for some reason this fails, you can always run the `/setup` command in the server to have it scan all the past messages. *WARNING* this will take a long time.  
  - If you need to force the setup command after it has been ran you can use the `/setup-force` command.
  - If you need to wipe the database clear because of messed up data you can run the `/wipe-server-data` command. 


## Tech Used:
* **Python 3** 
* **discord.py**
  - Used to create the bot on discord as well as create all the commands.
* **SQLite3**
  - Used to create the database where all the message data is stored. 

## Invite the Bot to Your Server

You can add the bot to your own server using the invite link:
https://discord.com/oauth2/authorize?client_id=1514369908085887037&permissions=8&integration_type=0&scope=bot+applications.commands


Or join this test server with the bot to test out the commands:
https://discord.gg/g87c4mmTg



PLEASE give me a bunch of stardust!!! 😁
