import DEFAULTConfig as defaultconfig
import DiscordUtil as discordutil
from discord.ext import commands, tasks
import google.generativeai as genai
import discord
import asyncio
import re
import time

# Configure Gemini API
genai.configure(api_key=defaultconfig.GEMINI_SDK)

DISCORD_MAX_MESSAGE_LENGTH = 2000
PLEASE_TRY_AGAIN_ERROR_MESSAGE = 'Problème, veuillez recommencer'

class GeminiAgent(commands.Cog):
    """
    Cog gérant l'IA Gemini et la modération autonome.
    Optimisé pour réduire les appels IA et éviter les quotas.
    """

    def __init__(self, bot):
        self.bot = bot
        self.model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
        self.chats = {}
        self.infractions = {}
        self.appeals = []
        self.log_channel_name = 'mod-logs'

        # Multi-critères
        self.message_times = {}
        self.spam_threshold = 5
        self.spam_window = 10
        self.blacklist_domains = ['malware.com', 'phish.com']
        self.profanity_list = ['idiot', 'connard', 'nique']
        self.self_harm_keywords = ['suicide', 'me tuer', 'kill myself']

        # Cooldown IA
        self.ai_cooldown = 60  # secondes par utilisateur
        self.last_ai_call = {}  # user_id -> timestamp

        # Surveillance proactive
        self.scanned_messages = set()
        self.proactive_scan.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content == 'ping gemini-agent' and not message.author.bot:
            await message.channel.send('AI à votre service !')
            return

        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return

        # Ignorer commandes prefixées !
        if message.content.startswith('!'):
            await self.bot.process_commands(message)
            return

        # Analyse modération
        await self.analyze_message(message)

    async def analyze_message(self, message):
        user_id = message.author.id
        content = message.content or ''
        print(f"[DEBUG] Analyse du message de {message.author}: {content}")

        # 1. Self-harm
        if any(kw in content.lower() for kw in self.self_harm_keywords):
            print(f"[CONSOLE] Alerte self-harm pour {message.author}")
            try:
                await message.author.send(
                    "Il semble que vous traversez des moments difficiles. Contactez une ligne d'écoute ou un professionnel."
                )
            except discord.Forbidden:
                pass
            return

        # 2. Spam detection
        now = time.time()
        times = self.message_times.setdefault(user_id, [])
        times = [t for t in times if now - t < self.spam_window]
        times.append(now)
        self.message_times[user_id] = times
        if len(times) > self.spam_threshold:
            reason = f'Spam détecté ({len(times)} msgs/{self.spam_window}s)'
            print(f"[CONSOLE] {reason}")
            await self._handle_infraction(message, reason)
            return

        # 3. Liens blacklistés
        for url in re.findall(r"https?://[^\s]+", content):
            domain = re.sub(r"https?://", '', url).split('/')[0]
            if domain in self.blacklist_domains:
                reason = f'Lien malveillant détecté: {domain}'
                print(f"[CONSOLE] {reason}")
                await self._handle_infraction(message, reason)
                return

        # 4. Profanités
        if any(word in content.lower() for word in self.profanity_list):
            reason = 'Contenu injurieux détecté'
            print(f"[CONSOLE] {reason}")
            await self._handle_infraction(message, reason)
            return

        # 5. IA Gemini en dernier recours avec cooldown
        last = self.last_ai_call.get(user_id, 0)
        if time.time() - last < self.ai_cooldown:
            print(f"[COOLDOWN] Ignoring IA call for {message.author} ({int(time.time()-last)}s since last).")
            return
        self.last_ai_call[user_id] = time.time()

        try:
            prompt = (
                f"Analyse ce message Discord pour modération : insultes, spam, contenu offensant ou dangereux. "
                f"Réponds par OUI/NON, puis raison concise.\n\n" f"\"{content}\""
            )
            response = await self.gemini_generate_content(user_id, prompt)
            print(f"[Analyse IA] {message.author}: {response}")
            if 'oui' in response.lower():
                await self._handle_infraction(message, response)
        except Exception as e:
            print(f"[Analyse IA] Erreur : {e}")

    async def _handle_infraction(self, message, reason):
        user = message.author
        count = self.infractions.get(user.id, 0) + 1
        self.infractions[user.id] = count
        try:
            await message.delete()
        except discord.Forbidden:
            print(f"[Erreur] Pas de permission pour supprimer {message.id}")

        if count == 1:
            await message.channel.send(f"⚠️ {user.mention}, avertissement #{count}. Raison : {reason}")
        elif count == 3:
            await self.mute_member(user, duration=600)
            await message.channel.send(f"🔇 {user.mention} mute (10 min) pour 3 avertissements.")
        elif count >= 5:
            await message.guild.ban(user, reason="Trop d'infractions")
            await message.channel.send(f"⛔️ {user.mention} banni(e) pour 5+ infractions.")

        try:
            await user.send(f"Votre message a été modéré. Raison : {reason}")
        except discord.Forbidden:
            print(f"[Erreur] Impossible d'envoyer DM à {user}")

    @commands.command()
    async def query(self, ctx, *, question):
        try:
            response = await self.gemini_generate_content(ctx.author.id, question)
            await ctx.send(response)
        except Exception as e:
            await ctx.send(PLEASE_TRY_AGAIN_ERROR_MESSAGE + f" ({e})")

    @commands.command()
    async def pm(self, ctx, *, question=None):
        try:
            dmchannel = await ctx.author.create_dm()
            if question is None:
                await dmchannel.send("Salut ! Pose-moi une question, et je te répondrai 🙂")
                return
            response = await self.gemini_generate_content(ctx.author.id, question)
            await dmchannel.send(response)
        except Exception as e:
            await ctx.send(PLEASE_TRY_AGAIN_ERROR_MESSAGE + f" ({e})")

    async def gemini_generate_content(self, user_id, content):
        if user_id not in self.chats:
            self.chats[user_id] = self.model.start_chat(history=[])
        chat = self.chats[user_id]
        try:
            response = await chat.send_message_async(content)
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            return PLEASE_TRY_AGAIN_ERROR_MESSAGE + f" ({e})"

    @tasks.loop(hours=1)
    async def proactive_scan(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name in ['mod-logs', 'mod-alerts']:
                    continue
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                async for msg in channel.history(limit=100):
                    if msg.id in self.scanned_messages or msg.author.bot:
                        continue
                    self.scanned_messages.add(msg.id)
                    await self.analyze_message(msg)

    @proactive_scan.before_loop
    async def before_proactive(self):
        await self.bot.wait_until_ready()
