import discord
from discord.ext import commands
import datetime
import os

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Не найден токен бота!")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.uptime = datetime.datetime.now(datetime.timezone.utc)

# Твой ID (замени на свой!)
OWNER_ID = 123456789012345678 

def get_admin_level(member):
    """Определяет уровень доступа пользователя."""
    if member.id == OWNER_ID:
        return 2
    
    admin_role = discord.utils.get(member.guild.roles, name="Admin")
    mod_role = discord.utils.get(member.guild.roles, name="Moderator")
    
    if admin_role and admin_role in member.roles:
        return 2
    if mod_role and mod_role in member.roles:
        return 1
        
    return 0

# --- СОБЫТИЯ ---

@bot.event
async def on_ready():
    print(f'✅ Бот запущен как {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Помощь: !help"))

# --- КОМАНДЫ УПРАВЛЕНИЯ АДМИНАМИ ---

@bot.command(name='add_admin')
@commands.is_owner()
async def add_admin(ctx, member: discord.Member, level: str = "admin"):
    guild = ctx.guild
    admin_role = discord.utils.get(guild.roles, name="Admin")
    if not admin_role:
        admin_role = await guild.create_role(name="Admin", permissions=discord.Permissions.administrator())
        
    mod_role = discord.utils.get(guild.roles, name="Moderator")
    if not mod_role:
        mod_role = await guild.create_role(name="Moderator", permissions=discord.Permissions(ban_members=True, kick_members=True, manage_messages=True))

    target_role = None
    if level.lower() == "mod":
        target_role = mod_role
        name = "Moderator"
    else:
        target_role = admin_role
        name = "Admin"

    try:
        await member.add_roles(target_role)
        await ctx.send(f"✅ Пользователь {member} получил роль **{name}** (Уровень {2 if name=='Admin' else 1})")
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на назначение роли.")

@bot.command(name='remove_admin')
@commands.is_owner()
async def remove_admin(ctx, member: discord.Member):
    guild = ctx.guild
    roles_to_remove = [r for r in member.roles if r.name in ["Admin", "Moderator"]]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)
        await ctx.send(f"🔻 Роль админа снята с {member}")
    else:
        await ctx.send(f"⚠️ У {member} нет ролей администратора.")

# --- КОМАНДА BROADCAST ---

@bot.command(name='broadcast')
@commands.is_owner()
async def broadcast(ctx, channel_id: str = None, *, message: str = ""):
    if not message:
        await ctx.send("Использование: `!broadcast <id_канала> <текст>`")
        return

    target_channel = None
    if channel_id:
        try:
            target_channel = bot.get_channel(int(channel_id))
            if not target_channel:
                await ctx.send("❌ Канал с таким ID не найден.")
                return
        except ValueError:
            await ctx.send("❌ Некорректный ID канала.")
            return
    else:
        target_channel = ctx.channel

    try:
        embed = discord.Embed(
            title="📢 ОБЪЯВЛЕНИЕ", 
            description=message, 
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Отправлено через бота | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        await target_channel.send(embed=embed)
        await ctx.send(f"✅ Сообщение отправлено в канал <#{target_channel.id}>")
    except Exception as e:
        await ctx.send(f"❌ Ошибка отправки: {e}")

# --- НОВЫЕ И ИСПРАВЛЕННЫЕ КОМАНДЫ ---

@bot.command(name='info', aliases=['h'])
async def info(ctx):
    embed = discord.Embed(title="📋 Меню Команд", color=discord.Color.blue())
    embed.add_field(name="Инфо", value="`!ping`, `!uptime`, `!server_info`, `!user_info @user`", inline=False)
    embed.add_field(name="Админ (Lvl 2)", value="`!broadcast <id> <текст>`, `!add_admin @user`", inline=False)
    embed.add_field(name="Модератор (Lvl 1+)", value="`!ban @user`, `!kick @user`, `!clear <кол-во>`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Пинг: `{latency} мс`')

@bot.command(name='uptime')
async def uptime(ctx):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - bot.uptime
    days, remainder = divmod(int(delta.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    embed = discord.Embed(title="⏱ Время работы", description=f"{days}д {hours}ч {minutes}м {seconds}с", color=discord.Color.purple())
    await ctx.send(embed=embed)

@bot.command(name='user_info')
async def user_info(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(title=f"👤 Информация о пользователе: {member}", color=member.top_role.color if member.top_role else discord.Color.greyple())
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Статус", value=str(member.status), inline=True)
    embed.add_field(name="Роли", value=f"{len(member.roles) - 1} ролей", inline=True)
    embed.add_field(name="Присоединился к Discord", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Присоединился к серверу", value=member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Неизвестно", inline=False)
    
    # Топ роль
    top_role = member.top_role
    if top_role.name != "@everyone":
        embed.add_field(name="Высшая роль", value=top_role.mention, inline=False)
        
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='server_info')
async def server_info(ctx):
    guild = ctx.guild
    owner = await guild.fetch_member(guild.owner_id)
    
    embed = discord.Embed(title=f"🏰 Информация о сервере: {guild.name}", color=guild.icon.color if guild.icon else discord.Color.greyple())
    embed.add_field(name="ID Сервера", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="Владелец", value=f"{owner} (`{owner.id}`)", inline=True)
    embed.add_field(name="Участники", value=f"{guild.member_count} всего", inline=True)
    embed.add_field(name="Боты", value=f"{sum(1 for m in guild.members if m.bot)}", inline=True)
    embed.add_field(name="Каналы", value=f"{len(guild.channels)} всего", inline=True)
    embed.add_field(name="Уровни верификации", value=str(guild.verification_level), inline=True)
    embed.add_field(name="Создан", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
    
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await ctx.send(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 100):
    # Discord API позволяет удалять только сообщения младше 14 дней одним запросом purge.
    # Если нужно больше — нужно писать кастомную функцию, но это медленнее.
    # Эта команда безопасна и не выдаст ошибку.
    deleted = await ctx.channel.purge(limit=amount + 1) # +1 чтобы удалить само сообщение команды
    
    # Удаляем сообщение бота об очистке через пару секунд
    await ctx.send(f"🧹 Очищено {len(deleted) - 1} сообщений.", delete_after=5)

# --- ЗАПУСК ---
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ Неверный токен!")
except KeyboardInterrupt:
    print("\n🛑 Бот остановлен.")
