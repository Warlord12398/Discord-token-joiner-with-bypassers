import aiohttp
import asyncio
import json
import threading

DISCORD_API = "https://discord.com/api/v9"

def get_token():
    
    try:
        with open("usertoken.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("[ERROR] usertoken.txt not found!")
        return None

async def send_request(session, url, method="POST", headers=None, json_data=None):
    """Sends an asynchronous request to Discord API."""
    async with session.request(method, url, headers=headers, json=json_data) as response:
        return response.status, await response.text()

async def join_server(token, invite_code):
    
    invite = invite_code.replace("https://discord.gg/", "").replace("discord.gg/", "")
    join_url = f"{DISCORD_API}/invites/{invite}"

    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        status, response = await send_request(session, join_url, headers=headers)
        
        if status == 200:
            print(f"[SUCCESS] Joined {invite_code}!")
            guild_id = json.loads(response).get("guild", {}).get("id")

            if guild_id:
                await bypass_onboarding(session, token, guild_id)
                await accept_rules(session, token, guild_id)
                await click_buttons(session, token, guild_id)  # Handles verification + role buttons
        else:
            print(f"[ERROR] Failed to join {invite_code} - {status}: {response}")

async def bypass_onboarding(session, token, guild_id):
    
    url = f"{DISCORD_API}/guilds/{guild_id}/onboarding"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    json_data = {"prompts": [], "actions": [], "mode": "complete"}
    status, response = await send_request(session, url, headers=headers, json_data=json_data)

    if status in [200, 204]:
        print(f"[SUCCESS] Bypassed onboarding for {guild_id}.")
    else:
        print(f"[ERROR] Onboarding bypass failed for {guild_id} - {status}: {response}")

async def accept_rules(session, token, guild_id):
    
    url = f"{DISCORD_API}/guilds/{guild_id}/member-verification"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    status, response = await send_request(session, url, "GET", headers=headers)

    if status == 200:
        verification_form = json.loads(response)
        rules_json = {"form_fields": verification_form["form_fields"], "version": verification_form["version"]}
        
        confirm_url = f"{DISCORD_API}/guilds/{guild_id}/requests/@me"
        status, response = await send_request(session, confirm_url, headers=headers, json_data=rules_json)

        if status in [200, 204]:
            print(f"[SUCCESS] Accepted rules for {guild_id}.")
        else:
            print(f"[ERROR] Failed to accept rules for {guild_id} - {status}: {response}")

async def click_buttons(session, token, guild_id):
    
    channels_url = f"{DISCORD_API}/guilds/{guild_id}/channels"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    status, response = await send_request(session, channels_url, "GET", headers=headers)

    if status == 200:
        channels = json.loads(response)
        for channel in channels:
            if channel.get("type") == 0:  
                await scan_buttons(session, token, channel["id"])
    else:
        print(f"[ERROR] Failed to fetch channels for {guild_id} - {status}: {response}")

async def scan_buttons(session, token, channel_id):
    
    messages_url = f"{DISCORD_API}/channels/{channel_id}/messages?limit=10"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    status, response = await send_request(session, messages_url, "GET", headers=headers)

    if status == 200:
        messages = json.loads(response)
        for message in messages:
            if "components" in message:
                for component in message["components"]:
                    for button in component["components"]:
                        if button["type"] == 2:  # Button type
                            await click_button(session, token, channel_id, message["id"], button["custom_id"])

async def click_button(session, token, channel_id, message_id, custom_id):
    """Sends a button click request."""
    click_url = f"{DISCORD_API}/interactions"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    json_data = {
        "type": 3,
        "guild_id": channel_id,
        "channel_id": channel_id,
        "message_id": message_id,
        "application_id": None,
        "session_id": "random",
        "data": {"component_type": 2, "custom_id": custom_id}
    }

    status, response = await send_request(session, click_url, headers=headers, json_data=json_data)

    if status in [200, 204]:
        print(f"[SUCCESS] Clicked button in {channel_id}.")
    else:
        print(f"[ERROR] Failed to click button - {status}: {response}")

def start_threaded_joins(token, invite_code):
    """Runs the join request using threading and asyncio."""
    async def run_async():
        await join_server(token, invite_code)

    thread = threading.Thread(target=asyncio.run, args=(run_async(),))
    thread.start()
    thread.join()

def main():
    """Main function to paste invite and join server."""
    token = get_token()
    if not token:
        return

    print("Paste your Discord invite link below and press Enter:")
    invite_code = input().strip()

    if invite_code:
        start_threaded_joins(token, invite_code)
    else:
        print("[ERROR] No valid invite code provided!")

if __name__ == "__main__":
    main()
