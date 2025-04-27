import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# Récupération des valeurs
DISCORD_OWNER_ID = config['DEFAULT'].get('discord_owner_id')
DISCORD_SDK = os.environ.get('DISCORD_SDK')  # Variable Render
GEMINI_SDK = os.environ.get('GEMINI_SDK')    # Variable Render

# Vérifications
if not DISCORD_SDK:
    raise ValueError("DISCORD_SDK manquant. Configurez-le sur Render !")
if not GEMINI_SDK:
    raise ValueError("GEMINI_SDK manquant. Configurez-le sur Render !")