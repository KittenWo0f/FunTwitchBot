from bot import Bot

bot = Bot('twitch_bot')
try:
    bot.run()
finally:
    bot.save_objects()
