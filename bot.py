import os
import discord
from discord.ext import commands, tasks
import random
import asyncio
import re

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ Переменная окружения DISCORD_TOKEN не найдена!")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

PREFIX = "!"

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- СОБЫТИЯ ---

@bot.event
async def on_ready():
    print(f"✅ Бот успешно запущен как {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"на {len(bot.guilds)} серверах | !menu"))
    if not status_loop.is_running():
        status_loop.start()

@tasks.loop(hours=1)
async def status_loop():
    pass 

@status_loop.error
async def error_handler(ctx, error):
    pass

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_embed_color(command_name):
    """Возвращает цвет в зависимости от категории команды"""
    colors = {
        "Информация": discord.Color.blue(),
        "Модерация": discord.Color.red(),
        "Развлечения": discord.Color.purple(),
        "Утилиты": discord.Color.green(),
        "Сервер": discord.Color.orange()
    }
    # Простая логика определения категории по имени команды
    if command_name in ["ping", "info", "serverinfo", "userinfo", "avatar"]:
        return colors["Информация"]
    elif command_name in ["ban", "kick", "rolecreate", "clear", "purge"]:
        return colors["Модерация"]
    elif command_name in ["roll", "random", "coinflip"]:
        return colors["Развлечения"]
    else:
        return colors["Утилиты"]

# --- КОМАНДЫ ---

@bot.command()
async def menu(ctx):
    """Показывает красивое меню всех команд"""
    
    embed = discord.Embed(
        title="📋 Меню Команд Бота",
        description="Выберите команду для выполнения:\n\n"
                    "Используй префикс `!` перед командой.\n\n"
                    f"**{ctx.author}**, вот полный список доступных функций:",
        color=discord.Color.gold()
    )

    # Категории команд
    categories = {
        "📊 Информация": [
            ("`!ping`", "Проверить задержку бота"),
            ("`!info`", "Статистика текущего сервера"),
            ("`!serverinfo`", "Подробная информация о сервере"),
            ("`!userinfo`", "Информация о пользователе (тебе)"),
            ("`!avatar`", "Показать аватарку профиля")
        ],
        "🛡️ Модерация": [
            ("`!clear <кол-во>`", "Очистить чат от сообщений"),
            ("`!kick <пользователь> [причина]`", "Выгнать пользователя с сервера"),
            ("`!ban <пользователь> [причина]`", "Забанить пользователя"),
            ("`!rolecreate <имя> [цвет]`", "Создать новую роль")
        ],
        "🎲 Развлечения": [
            ("`!random <min> <max>`", "Генерация случайного числа"),
            ("`!roll [d6/d20/2d6]`", "Бросок кубиков (напр. !roll d20)"),
            ("`!coinflip`", "Подбросить монетку")
        ]
    }

    for category, commands_list in categories.items():
        embed.add_field(
            name=category, 
            value="\n".join([f"{cmd}\n_Описание: {desc}_\n" for cmd, desc in commands_list]), 
            inline=False
        )

    embed.set_footer(text=f"Запрос от {ctx.author.display_name} • Версия 2.0")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    """Проверка задержки"""
    latency = round(bot.latency * 1000, 2)
    embed = discord.Embed(title="🏓 Pong!", description=f"Задержка: **{latency}ms**", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    """Общая статистика сервера"""
    server = ctx.guild
    embed = discord.Embed(
        title=f"📊 Статистика: {server.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Участников", value=len(server.members), inline=True)
    embed.add_field(name="🤖 Ботов", value=sum(1 for m in server.members if m.bot), inline=True)
    embed.add_field(name="🆕 Создан сервер", value=server.created_at.strftime("%d.%m.%Y"), inline=False)
    embed.set_footer(text=f"ID Сервера: {server.id}")
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, user: discord.User = None):
    """Показывает аватарку пользователя"""
    target = user or ctx.author
    embed = discord.Embed(
        title=f"Аватарка: {target.display_name}",
        color=discord.Color.random()
    )
    embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.set_footer(text=f"Нажми на картинку, чтобы открыть в полном размере")
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, user: discord.User = None):
    """Информация о пользователе"""
    target = user or ctx.author
    embed = discord.Embed(
        title=f"👤 Инфо о пользователе: {target.display_name}",
        color=discord.Color.dark_blue()
    )
    embed.add_field(name="🆔 ID", value=target.id, inline=True)
    embed.add_field(name="📅 Создан аккаунт", value=target.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
    embed.add_field(name="📥 Вступил на сервер", value=target.joined_at.strftime("%d.%m.%Y %H:%M") if target.joined_at else "Неизвестно", inline=True)
    embed.add_field(name="🎭 Текущий статус", value=target.status.value, inline=True)
    embed.add_field(name="🎨 Лучшая роль", value=target.top_role.mention if target.top_role != ctx.guild.default_role else "@everyone", inline=True)
    
    # Список ролей (обрезанный, если их много)
    roles = ", ".join([role.mention for role in target.roles[1:]][:10])
    if len(target.roles) > 10:
        roles += f" и еще {len(target.roles)-10}"
    embed.add_field(name="🏷 Роли", value=roles or "Нет ролей", inline=False)
    
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Детальная информация о сервере"""
    server = ctx.guild
    embed = discord.Embed(
        title=f"🏰 Информация о сервере: {server.name}",
        color=discord.Color.dark_vivid_purple()
    )
    embed.add_field(name="👑 Владелец", value=server.owner.mention, inline=True)
    embed.add_field(name="👥 Всего участников", value=len(server.members), inline=True)
    embed.add_field(name="🤖 Ботов", value=sum(1 for m in server.members if m.bot), inline=True)
    embed.add_field(name="📝 Текстовых каналов", value=len(server.text_channels), inline=True)
    embed.add_field(name="🔊 Голосовых каналов", value=len(server.voice_channels), inline=True)
    embed.add_field(name="🚩 Уровень верификации", value=str(server.verification_level), inline=True)
    embed.add_field(name="📅 Дата создания сервера", value=server.created_at.strftime("%d.%m.%Y"), inline=False)
    
    # Эмодзи
    emojis = ", ".join([str(e) for e in server.emojis[:10]])
    if len(server.emojis) > 10:
        emojis += f" (+{len(server.emojis)-10})"
    embed.add_field(name="😀 Эмодзи сервера", value=emojis or "Нет эмодзи", inline=False)
    
    embed.set_thumbnail(url=server.icon.url if server.icon else server.default_icon)
    embed.set_footer(text=f"ID Сервера: {server.id}")
    await ctx.send(embed=embed)

@bot.command()
async def clear(ctx, amount: int = 50):
    """Очистка чата (удаляет последние N сообщений + свою команду)"""
    if amount < 1 or amount > 100:
        return await ctx.send("❌ Укажи число от 1 до 100")
    
    # Discord API позволяет удалять только сообщения старше 2 недель одним запросом
    # Поэтому мы используем асинхронную очистку
    deleted = await ctx.channel.purge(limit=amount + 1) # +1 чтобы удалить саму команду
    
    embed = discord.Embed(
        title="🧹 Чат очищен",
        description=f"Удалено сообщений: **{amount}**",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed, delete_after=5)

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    """Кик пользователя"""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="🚪 Кик",
            description=f"**{member.display_name}** был выгнан с сервера.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на кик этого пользователя.")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    """Бан пользователя"""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Бан",
            description=f"**{member.display_name}** был забанен.",
            color=discord.Color.red()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на бан этого пользователя.")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command()
async def rolecreate(ctx, name: str, *, color: str = "blue"):
    """Создание новой роли"""
    # Парсинг цвета
    color_map = {
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "blue": discord.Color.blue(),
        "yellow": discord.Color.yellow(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
        "default": discord.Color.default()
    }
    
    embed_color = color_map.get(color.lower(), discord.Color.random())
    
    try:
        role = await ctx.guild.create_role(name=name, color=embed_color)
        embed = discord.Embed(
            title="✅ Роль создана",
            description=f"Роль **{role.name}** успешно создана!",
            color=embed_color
        )
        embed.add_field(name="ID Роли", value=role.id, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при создании роли: {e}")

@bot.command()
async def random(ctx, min_val: int, max_val: int):
    """Генерация случайного числа"""
    num = random.randint(min_val, max_val)
    embed = discord.Embed(
        title="🎲 Случайное число",
        description=f"Число между **{min_val}** и **{max_val}**: \n\n **{num}**",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.command()
async def roll(ctx, dice_expr: str = "d6"):
    """Бросок кубиков. Синтаксис: NdX (напр. 2d6, 1d20, d4)"""
    pattern = r'^(\d+)?d(\d+)$'
    match = re.match(pattern, dice_expr.lower())
    
    if not match:
        return await ctx.send("❌ Неверный формат. Используй например: `d6`, `2d6`, `1d20`")
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    
    if sides < 2 or count < 1:
        return await ctx.send("❌ Кубиков должно быть >= 1, граней >= 2")
        
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    
    embed = discord.Embed(
        title=f"🎲 Бросок: {dice_expr}",
        description=f"Результаты: `{', '.join(map(str, rolls))}`\n\n**Итого: {total}**",
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    """Подбрасывание монетки"""
    result = random.choice(["Орел 🪙", "Решка 🔄"])
    embed = discord.Embed(
        title="🪙 Монетка",
        description=f"Выпало: **{result}**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# --- ЗАПУСК ---
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ Неверный токен! Проверь переменную DISCORD_TOKEN")
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
