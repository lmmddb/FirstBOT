import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
from keep_alive import keep_alive

print("Lancement du bot...")            
bot = commands.Bot(command_prefix ="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot allumé !")
    # Synchroniser les commandes
    try : 
        synced = await bot.tree.sync()
        print (f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e :
        print(e)

@bot.event 
async def on_message(message : discord.Message):
    if message.author.bot: 
        return

    if message.content == 'Bonjour':
        channel = message.channel
        author = message.author
        await channel.send ("Bonjour, comment tu vas ?")
        await author.send ("Bonjour, comment tu vas ?")

@bot.tree.command(name="warning", description="Alerter une personne")
async def warning (interaction : discord.Interaction, member : discord.Member) : 
    await interaction.response.send_message ("Alerte envoyé !")
    await member.send ("Tu as reçu une alerte")

@bot.tree.command(name="ban", description="Bannir une personne")
async def ban (interaction : discord.Interaction, member : discord.Member) : 
    await interaction.response.send_message ("Ban envoyé !")
    await member.ban (reason= "???")
    await member.send ("Tu as été banni(e).")

@bot.tree.command(name="test", description="Tester les embeds")
async def test (interaction : discord.Interaction) :
    embed = discord.Embed(
    title = "Test title",
    description = "Description de l'embed",
    color = discord.Color.blurple())
    
    embed.add_field(name="Python", value="Apprendre Python en s'amusant")
    await interaction.response.send_message(embed=embed)

    
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN')) 






