import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

import DEFAULTConfig as defaultconfig
import DiscordUtil as discordUtil

import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from cogs.GeminiCog import GeminiAgent

load_dotenv()
print("Lancement du bot…")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')


@bot.event
async def on_ready():
    print("Bot allumé !")
    try:
        await bot.add_cog(GeminiAgent(bot))
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"[on_ready] Erreur : {e}")


@bot.tree.command(name="infractions", description="Afficher le nombre d’infractions d’un membre")
async def infractions(interaction: discord.Interaction, member: discord.Member):
    cog = bot.get_cog("GeminiAgent")
    if not cog:
        return await interaction.response.send_message("Cog de modération indisponible.", ephemeral=True)
    count = cog.get_infraction_count(member.id)
    embed = discord.Embed(
        title="Nombre d’infractions",
        description=f"{member.mention} a **{count}** infraction(s).",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stats", description="Afficher le dashboard de modération")
async def stats(interaction: discord.Interaction):
    cog = bot.get_cog("GeminiAgent")
    if not cog:
        return await interaction.response.send_message("Cog de modération indisponible.", ephemeral=True)
    data = cog.get_stats()  # doit renvoyer dict { total:…, warns:…, mutes:…, bans:… }
    embed = discord.Embed(title="📊 Dashboard de modération", color=discord.Color.blue())
    embed.add_field(name="Total d’infractions", value=str(data["total"]), inline=True)
    embed.add_field(name="Avertissements",     value=str(data["warns"]), inline=True)
    embed.add_field(name="Mises en mute",      value=str(data["mutes"]), inline=True)
    embed.add_field(name="Bans automatiques",  value=str(data["bans"]),  inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="appeal", description="Contester une sanction")
async def appeal(interaction: discord.Interaction, *, reason: str):
    cog = bot.get_cog("GeminiAgent")
    if not cog:
        return await interaction.response.send_message("Cog de modération indisponible.", ephemeral=True)
    cog.record_appeal(interaction.user.id, reason)
    await interaction.response.send_message(
        "✅ Votre appel a bien été enregistré. Les modérateurs vont l’examiner.",
        ephemeral=True
    )
    mod_alerts = discord.utils.get(interaction.guild.text_channels, name="mod-alerts")
    if mod_alerts:
        await mod_alerts.send(f"🚨 **Appeal** de {interaction.user.mention} :\n> {reason}")


@bot.command(aliases=["about"])
async def help(ctx):
    embed = discord.Embed(
        title="Commandes disponibles",
        description="""
**Slash commands**  
• /infractions @membre — nombre d’infractions  
• /stats               — dashboard de modération  
• /appeal raison       — contester une sanction  
""",
        color=discord.Color.dark_purple()
    )
    await ctx.send(embed=embed)


keep_alive()

bot.run(os.getenv('DISCORD_SDK'))
