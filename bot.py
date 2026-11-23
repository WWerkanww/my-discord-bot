import discord
from discord.ext import commands
import os
import time
from datetime import timedelta
from collections import defaultdict

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Ошибка: Переменная окружения DISCORD_TOKEN не найдена!")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

PREFIX = '!'
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- СИСТЕМА АНТИ-DDOS / АНТИ-СПАМ ---

class AntiSpamSystem:
    def __init__(self):
        self.ban_threshold = 20  # Лимит сообщений
        self.ban_window = 5      # Время окна (секунды)
        self.user_spam_data = defaultdict(lambda: {"messages": [], "banned": False})

    def check_spam(self, user, message):
        now = time.time()
        data = self.user_spam_data[user.id]
        
        data["messages"].append(now)
        # Очистка старых записей
        data["messages"] = [t for t in data["messages"] if now - t < self.ban_window]
        
        if len(data["messages"]) > self.ban_threshold and not data["banned"]:
            data["banned"] = True
            return True
        return False

anti_spam = AntiSpamSystem()

@bot.listen('on_message')
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Проверка спамом
    if anti_spam.check_spam(message.author, message):
        try:
            # Временная блокировка на 10 минут
            await message.author.timeout_until(discord.utils.utcnow() + timedelta(minutes=10))
            await message.channel.send(f"⚠️ Пользователь {message.author} заблокирован за спам/флуд!")
        except discord.Forbidden:
            pass # Если у бота нет прав на таймаут
        
    await bot.process_commands(message)

# --- КОМАНДЫ ---

@bot.command()
async def ping(ctx):
    """Проверка задержки"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", description=f"Задержка: `{latency}ms`", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    """Информация о сервере"""
    embed = discord.Embed(
        title=f"📊 Статистика: {ctx.guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Владелец", value=ctx.guild.owner.mention, inline=False)
    embed.add_field(name="👥 Участников", value=len(ctx.guild.members), inline=False)
    embed.add_field(name="📢 Каналов", value=len(ctx.guild.channels), inline=False)
    embed.set_footer(text=f"ID Сервера: {ctx.guild.id}")
    await ctx.send(embed=embed)

@bot.command()
async def delete_channel(ctx, channel_name: str, amount: int = 1):
    """Удаляет N каналов по имени."""
    all_channels = list(ctx.guild.channels)
    matching = [ch for ch in all_channels if ch.name == channel_name]
    
    if not matching:
        return await ctx.send(f"❌ Каналов с именем '{channel_name}' не найдено.")

    to_delete = matching[:amount]
    count = 0
    for ch in to_delete:
        try:
            await ch.delete(reason=f"Удалено через !delete_channel")
            count += 1
        except Exception:
            pass
            
    await ctx.send(f"✅ Удалено {count}/{amount} каналов.")

@bot.command()
async def create_channels(ctx, count: int, prefix: str = "канал"):
    """Создает N каналов."""
    created = 0
    for i in range(count):
        name = f"{prefix}_{i+1}"
        try:
            await ctx.guild.create_text_channel(name=name)
            created += 1
        except:
            break
    await ctx.send(f"✅ Создано {created}/{count} каналов.")

@bot.command()
async def purge(ctx, amount: int = 10):
    """Очищает чат от сообщений."""
    if 1 <= amount <= 100:
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🧹 Очищено {len(deleted)} сообщений.", delete_after=3)
    else:
        await ctx.send("❌ Укажите число от 1 до 100.")

@bot.command()
async def raid_mode(ctx, enabled: bool = True):
    """Включает режим рейда (выдача роли новичков)."""
    role_name = "Новичок"
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        role = await ctx.guild.create_role(name=role_name)
    
    if enabled:
        for member in ctx.guild.members:
            try: await member.add_roles(role)
            except: pass
        await ctx.send(f"🛡️ Режим рейда ВКЛЮЧЕН. Роль '{role_name}' выдана всем.")
    else:
        for member in ctx.guild.members:
            try: await member.remove_roles(role)
            except: pass
        await ctx.send(f"🛡️ Режим рейда ВЫКЛЮЧЕН.")

# --- НОВАЯ КОМАНДА: МЕНЮ / HELP ---
@bot.command()
async def menu(ctx):
    """Открывает меню со всеми командами бота"""
    embed = discord.Embed(
        title="📜 Меню Команд Бота",
        description="Выберите команду для выполнения:",
        color=discord.Color.purple()
    )
    
    # Список команд с описанием
    commands_list = [
        ("`!ping`", "Проверить работу бота"),
        ("`!info`", "Статистика сервера"),
        ("`!delete_channel <имя> <кол-во>`", "Удалить каналы (напр. `!delete_channel test 5`)"),
        ("`!create_channels <кол-во> <префикс>`", "Создать каналы"),
        ("`!purge <кол-во>`", "Очистить чат от сообщений"),
        ("`!raid_mode true/false`", "Включить/выключить защиту от рейдов"),
        ("`!menu`", "Показать это меню")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
        
    embed.set_footer(text=f"Бот работает | Запрос от {ctx.author.name}")
    await ctx.send(embed=embed)

# --- ЗАПУСК ---
print("Запуск бота...")
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("Ошибка авторизации: проверьте токен.")
except Exception as e:
    print(f"Ошибка запуска: {e}")
