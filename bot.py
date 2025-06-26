import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
import time

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', '')

# Aggressive but safe rate limiting for speed
MAX_CONCURRENT_REQUESTS = 100  # High concurrency
REQUEST_DELAY = 0.1  # Very short delay
BATCH_SIZE = 200  # Larger batches
BATCH_DELAY = 2  # Short delay between batches
STEAM_ACCOUNTS = [
    
        '76561199776778323', '76561199776519148', '76561199776765881', '76561199776773665', '76561199777137409', '76561199778301113',
        '76561199777290145', '76561199777416237', '76561199776413856', '76561199777664420', '76561199777178851', '76561199777008646',
        '76561199776950655', '76561199776749627', '76561199775633880', '76561199777566619', '76561199776583911', '76561199776866998',
        '76561199776782227', '76561199776452580', '76561199776750489', '76561199776765019', '76561199778202865', '76561199776679066',
        '76561199776312145', '76561199776848167', '76561199777231303', '76561199776668413', '76561199777620857', '76561199777341398',
        '76561199777534814', '76561199776787826', '76561199777390648', '76561199776411243', '76561199777846520', '76561199778023062',
        '76561199777088174', '76561199777242189', '76561199776782999', '76561199776835423', '76561199776952380', '76561199776370086',
        '76561199776791324', '76561199777400152', '76561199777448503', '76561199777059451', '76561199778212435', '76561199777846951',
        '76561199776829668', '76561199776229503', '76561199777216039', '76561199776829668', '76561199777846951', '76561199776229503', 
        '76561199776632484', '76561199777186611', '76561199778202003', '76561199776532565', '76561199776785377', '76561199776816114',
        '76561199776874133', '76561199776445327', '76561199777295649', '76561199777470481', '76561199776835854', '76561199777355686',
        '76561199776263191', '76561199777713834', '76561199776030449', '76561199776884622', '76561199777466584', '76561199777447756',
        '76561199777082106', '76561199777013901', '76561199776781275', '76561199776322166', '76561199776855272', '76561199777211806',
        '76561199776597311', '76561199776841552', '76561199776616821', '76561199777075077', '76561199776809043', '76561199777402783',
        '76561199776451475', '76561199777160576', '76561199777394270', '76561199778201572', '76561199776771450', '76561199776586696',
        '76561199776510272', '76561199777115633', '76561199776862423', '76561199776178935', '76561199777169015', '76561199777732585',
        '76561199776841333', '76561199443060440', '76561199777216039', '76561199777475176', '76561199778300682',

]

DATA_FILE = 'friend_data.json'
INIT_FILE = '.initialized'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteamFriendIDMonitor")

# Rate limiting semaphore
rate_limit_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def get_profile_link(steam_id):
    """Generate Steam profile link from Steam ID"""
    return f"steamcommunity.com/profiles/{steam_id}"

async def fetch_friend_list(session, steam_id):
    """Fetch the complete friend list for a Steam account with optimized rate limiting"""
    async with rate_limit_semaphore:
        url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"
        profile_link = get_profile_link(steam_id)
        
        # Minimal delay for speed
        if REQUEST_DELAY > 0:
            await asyncio.sleep(REQUEST_DELAY)
        
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    friends_data = data.get('friendslist', {}).get('friends', [])
                    friend_ids = [friend['steamid'] for friend in friends_data]
                    return steam_id, profile_link, friend_ids
                elif resp.status == 403:
                    # Private account - return empty list instead of None for faster processing
                    return steam_id, profile_link, []
                elif resp.status == 429:
                    logger.warning(f"Rate limited for {profile_link}")
                    # Don't retry immediately, just return None and continue
                    return steam_id, profile_link, None
                else:
                    logger.warning(f"{profile_link}: API error {resp.status}")
                    return steam_id, profile_link, None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {profile_link}")
            return steam_id, profile_link, None
        except Exception as e:
            logger.warning(f"Error fetching {profile_link}: {e}")
            return steam_id, profile_link, None

async def send_telegram_message(message):
    """Send message to Telegram, splitting if too long"""
    MAX_MESSAGE_LENGTH = 4000
    
    if len(message) <= MAX_MESSAGE_LENGTH:
        await _send_single_message(message)
    else:
        lines = message.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk + line + '\n') > MAX_MESSAGE_LENGTH:
                if current_chunk:
                    await _send_single_message(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    await _send_single_message(line[:MAX_MESSAGE_LENGTH])
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            await _send_single_message(current_chunk.strip())

async def _send_single_message(message):
    """Send a single message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload, timeout=5) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to send message: {await resp.text()}")
                else:
                    logger.info("Telegram message sent successfully")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

def load_previous_data():
    """Load previous friend data from file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    """Save friend data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_first_run():
    """Check if this is the first run of the bot"""
    if os.path.exists(INIT_FILE):
        return False
    with open(INIT_FILE, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

async def process_accounts_fast(steam_accounts):
    """Process accounts in optimized batches for speed"""
    results = []
    total_batches = (len(steam_accounts) + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Use a single session for all requests to improve performance
    connector = aiohttp.TCPConnector(limit=200, limit_per_host=100)
    timeout = aiohttp.ClientTimeout(total=600, connect=10)  # 10 minute total timeout
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(0, len(steam_accounts), BATCH_SIZE):
            batch = steam_accounts[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} accounts)")
            batch_start = time.time()
            
            # Process batch concurrently
            tasks = [fetch_friend_list(session, steam_id) for steam_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = 0
            for result in batch_results:
                if not isinstance(result, Exception) and result[2] is not None:
                    results.append(result)
                    successful += 1
            
            batch_time = time.time() - batch_start
            logger.info(f"Batch {batch_num} completed in {batch_time:.1f}s, {successful}/{len(batch)} successful")
            
            # Short delay between batches only if we have more batches
            if i + BATCH_SIZE < len(steam_accounts) and BATCH_DELAY > 0:
                await asyncio.sleep(BATCH_DELAY)
    
    return results

async def check_accounts():
    """Main function to check all accounts for friend changes - optimized for speed"""
    first_run = is_first_run()
    previous_data = load_previous_data()
    current_data = {}
    all_new_friends = []
    
    logger.info(f"Starting FAST friend check for {len(STEAM_ACCOUNTS)} accounts...")
    start_time = time.time()
    
    # Process all accounts with optimized batching
    results = await process_accounts_fast(STEAM_ACCOUNTS)
    
    processing_time = time.time() - start_time
    logger.info(f"Completed processing {len(results)} accounts in {processing_time:.2f} seconds")
    logger.info(f"Processing rate: {len(results)/processing_time:.1f} accounts/second")

    # Process results quickly
    for steam_id, profile_link, friend_ids in results:
        if friend_ids is None:
            continue
            
        current_data[steam_id] = {
            'profile_link': profile_link,
            'friends': friend_ids,
            'count': len(friend_ids)
        }
        
        # Skip change detection on first run
        if first_run or steam_id not in previous_data:
            continue
            
        previous_friends = set(previous_data[steam_id].get('friends', []))
        current_friends = set(friend_ids)
        
        # Check for new friends only
        new_friends = current_friends - previous_friends
        if new_friends:
            for friend_id in new_friends:
                friend_profile_link = get_profile_link(friend_id)
                all_new_friends.append(friend_profile_link)

    # Send notifications
    if all_new_friends and not first_run:
        if len(all_new_friends) == 1:
            msg = f"New friend: {all_new_friends[0]}"
        else:
            msg = f"New friends detected ({len(all_new_friends)}):\n\n"
            msg += "\n".join([f"• {friend_link}" for friend_link in all_new_friends])
        
        await send_telegram_message(msg)
        logger.info(f"Sent notification for {len(all_new_friends)} new friends")

    # Save data
    save_data(current_data)

    # Final statistics
    total_time = time.time() - start_time
    successful_accounts = len(current_data)
    failed_accounts = len(STEAM_ACCOUNTS) - successful_accounts
    total_friends = sum(data['count'] for data in current_data.values())
    
    logger.info(f"=== FINAL STATS ===")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Successful accounts: {successful_accounts}")
    logger.info(f"Failed/private accounts: {failed_accounts}")
    logger.info(f"Total friends tracked: {total_friends}")
    logger.info(f"New friends found: {len(all_new_friends)}")
    logger.info(f"Average processing rate: {successful_accounts/total_time:.1f} accounts/second")

if __name__ == '__main__':
    asyncio.run(check_accounts())
