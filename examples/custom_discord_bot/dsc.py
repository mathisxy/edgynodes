import os
import discord
from discord.ext import commands
from logger import setup_logger
from dotenv import load_dotenv
from message_handling import handle_message

# Logger
logger = setup_logger(__name__)
# Environment
load_dotenv()


# Discord Intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
intents.presences = True
intents.voice_states = True 

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_message(message: discord.Message):
    try:
        await handle_message(message, bot)
    except Exception as e:
        logger.exception(e)
        await message.reply(str(e))


@bot.event
async def on_ready():
    print(f"🤖 Bot online as {bot.user}!")

print(os.getenv("DISCORD_TOKEN", ""))
bot.run(os.getenv("DISCORD_TOKEN", ""))