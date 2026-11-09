import os
import asyncio
import threading
import time
import logging
from flask import Flask, request, jsonify, render_template_string
import discord
from discord.ext import commands, tasks

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ FLASK САЙТА ---
app = Flask(__name__)

# Глобальная переменная для хранения статуса последнего сообщения
last_broadcast_msg = None

@app.route('/')
def home():
    return """
    <h1>Панель управления Discord Ботом</h1>
    
    <h3>1. Глобальная рассылка (GlobalMsg)</h3>
    <form action="/globalmsg" method="POST">
        <label>IDs каналов (через запятую):</label><br>
        <input type="text" name="channels" placeholder="123456789, 987654321" required><br><br>
        
        <label>Текст сообщения:</label><br>
        <textarea name="message" rows="4" cols="50" required></textarea><br><br>
        
        <button type="submit">Отправить</button>
    </form>
    <p id="status"></p>

    <hr>

    <h3>2. Отправка в текущий чат (!mes)</h3>
    <form action="/send_local" method="POST">
        <label>Сообщение:</label><br>
        <input type="text" name="message" required><br><br>
        <button type="submit">Отправить</button>
    </form>
    <p id="local_status"></p>
    """

@app.route('/globalmsg', methods=['POST'])
def handle_global_msg():
    channels = request.form.get('channels')
    message = request.form.get('message')
    
    if not bot.is_ready():
        return "Бот еще не запустился!"

    # Запускаем функцию отправки в отдельном потоке или асинхронно
    # Но так как мы в синхронном Flask, лучше использовать loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(send_to_channels(channels, message))
        return f"<h3>Результат:</h3>{result}"
    finally:
        loop.close()

async def send_to_channels(channel_ids_str, text):
    ids_list = [id.strip() for id in channel_ids_str.split(',')]
    success_count = 0
    errors = []
    
    for cid in ids_list:
        try:
            cid_int = int(cid)
            ch = bot.get_channel(cid_int) or await bot.fetch_channel(cid_int)
            await ch.send(text)
            success_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            errors.append(f"Ошибка канала {cid}: {e}")
            
    return f"✅ Успешно: {success_count}<br>❌ Ошибки: {'<br>'.join(errors)}"

@app.route('/send_local', methods=['POST'])
def handle_send_local():
    message = request.form.get('message')
    if not bot.is_ready():
        return "Бот не готов"
    
    # Находим первый доступный канал (для примера)
    # В реальном проекте нужно выбирать канал через интерфейс
    guild = bot.guilds[0] if bot.guilds else None
    if not guild:
        return "Нет серверов"
    
    # Ищем текстовый канал
    text_channel = discord.utils.get(guild.text_channels)
    if text_channel:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(text_channel.send(message))
            return f"Сообщение отправлено в канал {text_channel.name}"
        finally:
            loop.close()
    return "Не удалось найти канал"

# --- DISCORD BOT CONFIGURATION ---

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True  # ВАЖНО для !clear и чтения истории
intents.members = True   # Важно для глобального бана и других действий

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот успешно запустился!')
    print(f'Имя: {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Управление через сайт"))
    
    # Запуск Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()

# --- КОМАНДЫ ---

@bot.command(name='помощь', aliases=['h'])
async def help_command(ctx):
    embed = discord.Embed(title="📋 Меню команд", color=discord.Color.blue())
    embed.add_field(name="!mes \"текст\"", value="Отправить сообщение и удалить команду", inline=False)
    embed.add_field(name="!clear <N>", value="Удалить N сообщений (нужны права Manage Messages)", inline=False)
    embed.add_field(name="!globalban @user", value="Забанить пользователя на всех серверах", inline=False)
    embed.add_field(name="!globalmsg \"id1,id2\" \"текст\"", value="Рассылка в несколько каналов", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='mes', aliases=['msg', 'm'])
async def send_message(ctx, *, text: str):
    """Отправить сообщение от имени бота и удалить команду"""
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass 
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на удаление сообщений!")
        return
        
    await ctx.send(content=text)

@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True) 
async def clear_messages(ctx, amount: int = 100):
    """Очистить чат от последних N сообщений"""
    if amount > 100:
        amount = 100
    
    try:
        deleted = await ctx.channel.purge(limit=amount + 1) 
        confirmation = await ctx.send(f"🧹 Удалено {len(deleted) - 1} сообщений!")
        await confirmation.delete(delay=5) 
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на удаление сообщений в этом канале.")

@bot.command(name='globalban', aliases=['gb'])
@commands.is_owner() 
async def global_ban(ctx, user: discord.User):
    total_guilds = len(bot.guilds)
    banned_count = 0
    failed_guilds = []
    
    status_msg = await ctx.send(f"Начинаю глобальный бан пользователя **{user}**...")
    
    for guild in bot.guilds:
        try:
            if not guild.me.guild_permissions.ban_members:
                continue
            await guild.ban(user, reason=f"Global ban by {ctx.author}")
            banned_count += 1
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            failed_guilds.append(guild.name)
        except Exception as e:
            failed_guilds.append(f"{guild.name}: {e}")
            
    result_embed = discord.Embed(
        title="🌍 Глобальный бан завершен",
        description=f"Пользователь **{user}** был забанен.",
        color=discord.Color.red()
    )
    result_embed.add_field(name="Успешно", value=f"{banned_count}/{total_guilds}", inline=False)
    if failed_guilds:
        result_embed.add_field(name="Ошибки", value="\n".join(failed_guilds[:5]), inline=False)
        
    await status_msg.edit(embed=result_embed)

@bot.command(name='globalmsg', aliases=['gmsg'])
@commands.is_owner() 
async def global_msg(ctx, channel_ids: str, *, text: str):
    """Рассылка в несколько каналов"""
    ids_list = [id.strip() for id in channel_ids.split(',')]
    success_count = 0
    fail_count = 0
    errors = []

    start_msg = await ctx.send(f"Отправка в **{len(ids_list)}** каналов...")

    for channel_id_str in ids_list:
        try:
            channel_id = int(channel_id_str)
            channel = bot.get_channel(channel_id)
            if channel is None:
                channel = await bot.fetch_channel(channel_id)
            
            await channel.send(text)
            success_count += 1
            await asyncio.sleep(0.5)
        except ValueError:
            fail_count += 1
            errors.append(f"{channel_id_str} - не число")
        except discord.Forbidden:
            fail_count += 1
            errors.append(f"Нет прав для {channel_id_str}")
        except Exception as e:
            fail_count += 1
            errors.append(f"Ошибка {channel_id_str}: {e}")

    report_embed = discord.Embed(
        title="📤 Рассылка завершена",
        description=f"Текст: `{text}`",
        color=discord.Color.green() if fail_count == 0 else discord.Color.yellow()
    )
    report_embed.add_field(name="✅ Успех", value=str(success_count), inline=True)
    report_embed.add_field(name="❌ Ошибки", value=str(fail_count), inline=True)
    
    await start_msg.edit(embed=report_embed)

# Запуск
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("Переменная окружения DISCORD_TOKEN не найдена!")
    
    # Запускаем бота
    bot.run(token)
