import requests
import time
import asyncio
import discord

# ======= CONFIGURE DISCORD CLIENT =======
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

# ======= CONFIGURE LOGGING =======
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ======= LOAD TOKENS FROM tokens.txt =======
def load_tokens():
    with open("tokens.txt", "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# ======= JOIN SERVER FUNCTION =======
def join_server(token, invite_code):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    invite_url = f"https://discord.com/api/v9/invites/{invite_code}"
    
    response = requests.post(invite_url, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"✅ Successfully joined with token: {token[:20]}...")
    elif response.status_code == 429:
        retry_after = response.json().get("retry_after", 5)
        logger.warning(f"⚠️ Rate limited! Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return join_server(token, invite_code)
    else:
        logger.error(f"❌ Failed to join with token {token[:20]}... | Status: {response.status_code} | Response: {response.text}")

# ======= DISCORD CLIENT FOR VOICE CHANNEL JOIN =======
class VoiceClient(discord.Client):
    def __init__(self, token, channel_id, mute, video):
        super().__init__(intents=intents)
        self.token = token
        self.channel_id = channel_id
        self.mute = mute
        self.video = video

    async def on_ready(self):
        logger.info(f"✅ Logged in as {self.user}")

        # Get the guild and voice channel
        for guild in self.guilds:
            channel = discord.utils.get(guild.voice_channels, id=int(self.channel_id))
            if channel:
                vc = await channel.connect()
                await asyncio.sleep(2)
                
                if not self.mute:
                    logger.info("🎙️ Joined the VC unmuted but staying silent.")

                if self.video:
                    logger.info("📹 Enabling profile picture as video (not supported in bot API)...")

                await asyncio.sleep(5)
                await vc.disconnect()
                await self.close()
                break

# ======= MAIN FUNCTION =======
def main():
    tokens = load_tokens()
    if not tokens:
        logger.error("❌ No tokens found in tokens.txt!")
        return

    print("1) Token Joiner")
    choice = input("Select an option: ")
    
    if choice == "1":
        invite_code = input("Enter the Discord invite code (e.g., discord.gg/yourserver): ").split("/")[-1]
        
        for token in tokens:
            join_server(token, invite_code)
            time.sleep(3)  # Prevents spamming requests too quickly

        join_vc = input("Join voice call? (Y/N): ").strip().lower()
        if join_vc == "y":
            vc_channel_id = input("Enter Voice Channel ID: ").strip()
            mute_option = input("Mute? (Y/N): ").strip().lower() == "y"
            video_option = input("Enable Video? (Y/N): ").strip().lower() == "y"

            for token in tokens:
                client = VoiceClient(token, vc_channel_id, mute_option, video_option)
                client.run(token, bot=False)  # Runs as a user account
                time.sleep(3)  # Prevents spamming requests too quickly

if __name__ == "__main__":
    main()
