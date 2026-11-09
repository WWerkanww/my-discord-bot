import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import json

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) # ID текстового канала, куда будем писать

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.http_app = None
        self.runner = None

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.start_http_server()

    async def start_http_server(self):
        app = aiohttp.web.Application()
        app.router.add_post('/webhook', self.handle_webhook)
        
        port = int(os.getenv('PORT', 8080))
        self.runner = aiohttp.web.AppRunner(app)
        await self.runner.setup()
        site = aiohttp.web.TCPSite(self.runner, '0.0.0.0', port)
        await site.start()
        print(f"HTTP Server running on port {port}")

    async def handle_webhook(self, request):
        try:
            data = await request.json()
            message_text = data.get('message', '')
            
            if not message_text:
                return aiohttp.web.Response(text="No message provided", status=400)

            channel = self.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(message_text)
                return aiohttp.web.Response(text="Success")
            else:
                return aiohttp.web.Response(text="Channel not found", status=500)
        except Exception as e:
            return aiohttp.web.Response(text=str(e), status=500)

# Запуск
bot = MyBot()

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

if __name__ == '__main__':
    bot.run(TOKEN)
