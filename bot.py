import discord
from discord.ext import commands
from aiohttp import web
import asyncio
import os

# --- НАСТРОЙКИ ---
TOKEN = 'MTU2ODk4NDI4ODM3NDk1MjAwOA.Gx2xXd.r5rBTcrv7ZgdtVVKzPV0n00OpsD_nkxz3GbNH4'
CHANNEL_ID = 1569350540381393058

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Глобальная переменная для сервера
server_task = None

@bot.event
async def on_ready():
    print(f'{bot.user} успешно подключился!')
    
    global server_task
    if server_task is None or server_task.done():
        server_task = asyncio.create_task(start_http_server())

async def start_http_server():
    app = web.Application()
    app.router.add_post('/webhook', handle_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    # Railway использует порт 8080
    site = web.TCPSite(runner, '0.0.0.0', 8080) 
    await site.start()
    print("HTTP Сервер запущен на порту 8080")

async def handle_webhook(request):
    try:
        data = await request.json()
        content = data.get('content', '')
        
        if not content:
            return web.Response(text="Нет текста", status=400)

        # Получаем канал по ID
        channel = bot.get_channel(CHANNEL_ID)
        
        if channel:
            await channel.send(content)
            return web.Response(text="Отправлено", status=200)
        else:
            print(f"Канал с ID {CHANNEL_ID} не найден!")
            return web.Response(text="Канал не найден", status=404)
            
    except Exception as e:
        print(f"Ошибка обработки запроса: {e}")
        return web.Response(text="Ошибка сервера", status=500)

if __name__ == "__main__":
    bot.run(TOKEN)
