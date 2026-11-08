import os
import asyncio
import discord
from discord.ext import commands

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот успешно запустился!')
    print(f'Имя: {bot.user}')
    
    # Изменение статуса
    await bot.change_presence(activity=discord.Game(name="!помощь"))

# --- Команды ---

@bot.command(name='помощь', aliases=['h'])
async def help_command(ctx):
    """Показать меню всех команд"""
    embed = discord.Embed(
        title="📋 Меню команд",
        description="Вот список доступных команд:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="!mes \"текст\"", value="Отправить сообщение от имени бота и удалить вызов", inline=False)
    embed.add_field(name="!id", value="Получить ID текущего пользователя или канала", inline=False)
    embed.add_field(name="!server_info", value="Информация о текущем сервере", inline=False)
    embed.add_field(name="!clear <N>", value="Удалить последние N сообщений (нужно право Manage Messages)", inline=False)
    embed.add_field(name="!globalban @user", value="Забанить пользователя на ВСЕХ серверах бота", inline=False)
    
    embed.set_footer(text=f"Запросил: {ctx.author.name}#{ctx.author.discriminator}")
    await ctx.send(embed=embed)

@bot.command(name='mes', aliases=['msg', 'm'])
async def send_message(ctx, *, text: str):
    """Отправить сообщение от имени бота и удалить команду"""
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass 
    
    await ctx.send(content=text)

@bot.command(name='id')
async def get_id(ctx):
    """Показать ID автора команды и канала"""
    embed = discord.Embed(title="ℹ️ Информация об ID", color=discord.Color.purple())
    embed.add_field(name="Твой ID", value=f"{ctx.author.id}", inline=False)
    embed.add_field(name="ID Канала", value=f"{ctx.channel.id}", inline=False)
    embed.add_field(name="ID Сервера", value=f"{ctx.guild.id if ctx.guild else 'DМ'}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='server_info', aliases=['si'])
async def server_info(ctx):
    """Информация о сервере"""
    guild = ctx.guild
    if guild is None:
        await ctx.send("Эта команда работает только на серверах.")
        return

    embed = discord.Embed(title=f"Информация о сервере: {guild.name}", color=discord.Color.blue())
    embed.add_field(name="👑 Владелец", value=guild.owner, inline=False)
    embed.add_field(name="👥 Участников", value=guild.member_count, inline=False)
    embed.add_field(name="📅 Создан", value=guild.created_at.strftime("%d.%m.%Y %H:%M"), inline=False)
    embed.add_field(name="🔢 Всего каналов", value=len(guild.channels), inline=False)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    await ctx.send(embed=embed)

@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True) 
async def clear_messages(ctx, amount: int = 100):
    """Очистить чат от последних N сообщений"""
    if amount > 100:
        amount = 100
        
    deleted = await ctx.channel.purge(limit=amount + 1) 
    
    confirmation = await ctx.send(f"Удалено {len(deleted) - 1} сообщений!")
    await confirmation.delete(delay=5) 

@bot.command(name='globalban', aliases=['gb'])
@commands.is_owner() # Только владелец бота может использовать эту команду
async def global_ban(ctx, user: discord.User):
    """Глобальный бан пользователя на всех серверах"""
    total_guilds = len(bot.guilds)
    banned_count = 0
    failed_guilds = []
    
    # Отправляем стартовое сообщение
    status_msg = await ctx.send(f"Начинаю глобальный бан пользователя **{user}**... (Всего серверов: {total_guilds})")
    
    for guild in bot.guilds:
        try:
            # Проверяем, есть ли у бота права на бан
            if not guild.me.guild_permissions.ban_members:
                continue
                
            await guild.ban(user, reason=f"Global ban by {ctx.author}")
            banned_count += 1
            
            # Небольшая задержка, чтобы избежать Rate Limit
            await asyncio.sleep(0.5)
            
        except discord.Forbidden:
            failed_guilds.append(guild.name)
        except Exception as e:
            failed_guilds.append(f"{guild.name}: {e}")
            
    # Формируем итоговое сообщение
    result_embed = discord.Embed(
        title="🌍 Глобальный бан завершен",
        description=f"Пользователь **{user}** был забанен.",
        color=discord.Color.red()
    )
    result_embed.add_field(name="Успешно забанено", value=f"{banned_count}/{total_guilds}", inline=False)
    
    if failed_guilds:
        result_embed.add_field(name="Ошибки/Нет прав", value="\n".join(failed_guilds[:10]), inline=False)
        if len(failed_guilds) > 10:
            result_embed.add_field(name="...", value=f"И еще {len(failed_guilds) - 10} серверов", inline=False)
            
    result_embed.set_footer(text=f"Выполнил: {ctx.author}")
    
    await status_msg.edit(embed=result_embed)

# Запуск
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("Переменная окружения DISCORD_TOKEN не найдена!")
    
    bot.run(token)
