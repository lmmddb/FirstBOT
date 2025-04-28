# FirstBOT

FirstBOT est un bot Discord écrit en Python, conçu pour proposer des fonctionnalités de modération et d'interaction automatique au sein de serveurs Discord. Il contient également un module d'intelligence artificielle basé sur Gemini.

## Fonctionnalités

- Répond à des commandes spécifiques (!query et !pm)
- Fonctionnalités de modération
- Maintien du bot en ligne avec un serveur 
- Configuration personnalisable via `DEFAULTConfig.py`
- Intégration de Gemini AI via 'GeminiCog.py'

## Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/lmmddb/FirstBOT.git
   cd FirstBOT
   ```

2. Installez les dépendances nécessaires :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurez le bot :
   - Renseignez votre token Discord et la clé API Gemini dans DEFAULTConfig.py.

4. Lancez le bot :
   ```bash
   python bot.py
   ```

## Fichiers importants

- `bot.py` : Code principal du bot
- `DEFAULTConfig.py` : Fichier de configuration
- `keep_alive.py` : Script pour maintenir le bot actif (utile pour l'hébergement sur certaines plateformes)
- `requirements.txt` : Liste des librairies nécessaires
- `geminiCog.py` : Gère les commandes liées à l'IA Gemini

## Prérequis

- Python 3.8 ou supérieur
- Un compte Discord et un bot Discord enregistré ([créer un bot ici](https://discord.com/developers/applications))
