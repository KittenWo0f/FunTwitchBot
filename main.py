from bot import twitch_bot
import sys

try:
    bot = twitch_bot('twitch_bot')
    bot.run()
except:
    sys.exit(1)
