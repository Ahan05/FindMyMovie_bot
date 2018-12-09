import os
from aiogram import Bot
# import aiosocksy


def make_bot():
    api_token = os.environ['BOT_API']

    # proxy_ip = os.environ['ProxyIP']
    # proxy_port = os.environ['ProxyPort']
    # proxy_user_name = os.environ['ProxyUserName']
    # proxy_pass = os.environ['ProxyPassword']

    # proxy_url = 'socks5://{}:{}'.format(proxy_ip, proxy_port)
    # proxy_auth = aiosocksy.Socks5Auth(login=proxy_user_name, password=proxy_pass)

    bot = Bot(token=api_token)
    print("Created bot")

    return bot
