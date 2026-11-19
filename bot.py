import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import random
import datetime
import aiohttp

# Получаем токены из переменных окружения Railway
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not DISCORD_TOKEN:
    raise ValueError("Переменная DISCORD_TOKEN не найдена в настройках Railway!")

# Настройки интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

# --- БАЗА ДАННЫХ (JSON) ---
DATA_FILE = 'bot_data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"warnings": {}, "xp": {}}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"warnings": {}, "xp": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Инициализация данных при запуске
bot_data = load_data()

# --- СИСТЕМА МОДЕРАЦИИ ---

@bot.command(name='warn')
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "Не указана"):
    user_id = str(member.id)
    if user_id not in bot_data['warnings']:
        bot_data['warnings'][user_id] = []
    
    bot_data['warnings'][user_id].append({
        "reason": reason,
        "moderator": ctx.author.display_name,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_data(bot_data)
    
    embed = discord.Embed(title="⚠️ Предупреждение", description=f"**Нарушение:** {reason}", color=discord.Color.orange())
    embed.set_footer(text=f"Всего варнов: {len(bot_data['warnings'][user_id])}")
    await ctx.send(embed=embed)

@bot.command(name='mute')
@commands.has_permissions(mute_members=True)
async def mute(ctx, member: discord.Member, duration: int = 60, *, reason: str = "Мут без причины"):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(muted_role, send_messages=False)
    
    await member.add_roles(muted_role)
    embed = discord.Embed(title="🔇 Мут выдан", description=f"**Длительность:** {duration} сек.\n**Причина:** {reason}", color=discord.Color.red())
    await ctx.send(embed=embed)
    
    await asyncio.sleep(duration)
    await member.remove_roles(muted_role)
    await ctx.send(f"✅ Мут для {member} истек.")

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = "Бан без причины"):
    await member.ban(reason=f"Ban by {ctx.author}: {reason}")
    embed = discord.Embed(title="👢 Бан", description=f"**Пользователь:** {member}\n**Причина:** {reason}", color=discord.Color.dark_red())
    await ctx.send(embed=embed)

# --- СИСТЕМА УРОВНЕЙ (XP) ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Добавляем XP
    user_id = str(message.author.id)
    if user_id not in bot_data['xp']:
        bot_data['xp'][user_id] = {"xp": 0, "level": 1}
    
    bot_data['xp'][user_id]['xp'] += random.randint(5, 15)
    current_xp = bot_data['xp'][user_id]['xp']
    level_up_threshold = bot_data['xp'][user_id]['level'] * 100
    
    if current_xp >= level_up_threshold:
        bot_data['xp'][user_id]['level'] += 1
        bot_data['xp'][user_id]['xp'] -= level_up_threshold
        
        embed = discord.Embed(title="🎉 Уровень повышен!", description=f"Поздравляем! Вы достигли **{bot_data['xp'][user_id]['level']}** уровня!", color=discord.Color.gold())
        await message.channel.send(embed=embed)
        
    save_data(bot_data)

@bot.command(name='rank')
async def rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)
    data = bot_data['xp'].get(user_id, {"xp": 0, "level": 1})
    
    progress = (data['xp'] / (data['level'] * 100)) * 100
    
    embed = discord.Embed(title=f"📊 Статистика: {target.display_name}", color=discord.Color.blue())
    embed.add_field(name="Уровень", value=data['level'], inline=True)
    embed.add_field(name="Опыт", value=f"{data['xp']} / {data['level'] * 100}", inline=True)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
    
    bar_length = 10
    filled = int(progress / 10)
    empty = bar_length - filled
    embed.description = f"[{'█' * filled}{'░' * empty}] {progress:.1f}%"
    
    await ctx.send(embed=embed)

# --- ИНТЕГРАЦИЯ С AI (CHATGPT) ---

@bot.command(name='ask')
async def ask_ai(ctx, *, question: str):
    if not OPENAI_API_KEY:
        await ctx.send("API ключ OpenAI не настроен в переменных среды.")
        return
    
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': question}],
            'max_tokens': 150
        }
        try:
            async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload) as resp:
                data = await resp.json()
                answer = data['choices'][0]['message']['content']
                await ctx.send(f"🤖 **AI ответ:**\n{answer}")
        except Exception as e:
            await ctx.send(f"Ошибка AI: {e}")

# --- АВТО-ПРИВЕТСТВИЕ ---

@bot.event
async def on_member_join(member):
    # Найди канал приветствия по имени или ID, если он есть
    welcome_channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if not welcome_channel:
        welcome_channel = member.guild.system_channel # Или другой канал по умолчанию
    
    if welcome_channel:
        embed = discord.Embed(title="Добро пожаловать!", description=f"{member.mention}, рад видеть тебя на сервере!", color=discord.Color.green())
        embed.set_image(url="https://media.giphy.com/media/26tn336PjAlV8JpGO/giphy.gif")
        await welcome_channel.send(embed=embed)

# Запуск бота
print("Бот запускается...")
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"Ошибка запуска: {e}")
