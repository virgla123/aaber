import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', '')

STEAM_ACCOUNTS = [

    '76561197997028404','76561198010608505','76561197995348064','76561198027225409','76561198087297348',
    '76561198033115279','76561198079929540','76561198101608719','76561198165806979','76561198102885877',
    '76561198214306592','76561198034408524','76561198199512505','76561198262845266','76561198212373968',
    '76561198271116426','76561198258289087','76561198016322289','76561198283520257','76561198197435149',
    '76561198113445521','76561198393861053','76561198152211922','76561198153784679','76561198133868972',
    '76561198206080048','76561198251214896','76561198120343724','76561198170788785','76561198160799267',
    '76561198150055795','76561198052391770','76561198121237658','76561198262275145','76561198893140741',
    '76561198799269590','76561198241926262','76561198197600818','76561198840655497','76561198859163957',
    '76561198345437523','76561198366194054','76561198345041158','76561198374688071','76561198150826247',
    '76561198362919361','76561198254060503','76561198398725087','76561198262917719','76561198161999383',
    '76561198988129034','76561198856908589','76561198388427126','76561198584383020','76561198969151592',
    '76561198271310542','76561198839498501','76561198813865423','76561198850917515','76561198908525837',
    '76561198876158184','76561198881772686','76561198449618981','76561198948231515','76561198815965686',
    '76561198813173189','76561198853628000','76561198810413486','76561198292932889','76561198958119408',
    '76561198370186657','76561198440017791','76561198950299533','76561198851287707','76561198798153445',
    '76561198842010196','76561198874615919','76561198408099499','76561198380128863','76561198799710966',
    '76561198401232954','76561198811520422','76561198328268217','76561198969038414','76561198866247742',
    '76561198370186657','76561198810413486','76561198432916219','76561198835864498','76561198803672914',
    '76561198869496180','76561198875839774','76561198877616862','76561198936673187','76561198427808098',
    '76561198880457893','76561198935875224','76561198118222557','76561198338092421','76561198206178276',
    
    '76561197991531660','76561197979012706','76561198004976810','76561197992938057','76561198001009416',
    '76561198001623622','76561198385712103','76561198037787857','76561198005698162','76561198018823565',
    '76561198046315252','76561198288809723','76561198977533205','76561198249712750','76561198354146673',
    
    '76561197987030746','76561197993482972','76561197997171109','76561197999889528','76561198008535006',
    '76561198010722601','76561198030223034','76561198020168829','76561198013750615','76561198062537256',
    '76561198180890550','76561198148875417','76561198049811674','76561198860958937','76561198344486567',
    '76561198355563061','76561198381298151','76561198254110089','76561198282255154','76561198833792958',
    '76561198310302063','76561198276342567','76561198142355472','76561198108221056','76561198069147103',
    
    '76561197989143464','76561197990318614','76561198003127315','76561198001216683','76561197998424730',
    '76561198007599050','76561198032674780','76561198013797596','76561198017675454','76561198035314895',
    '76561198204104416','76561198083854959','76561199001194976','76561198800017819','76561198796026462',
    '76561198207755559','76561198274787266','76561198952470129','76561198331262300','76561198195145282',
    
    
    '76561197977303576','76561197995279803','76561198002716679',
    '76561198001094806','76561198080145367','76561198013072288','76561198044529106','76561198012412170',
    '76561198028621775','76561198012273602','76561198841341084','76561198053160675','76561198087868387',
    '76561198297244107','76561198157129823','76561198996054101','76561198978727834','76561198440480389',
    '76561198964342821','76561198266094488','76561198208723744','76561198126278816','76561198102856479',
    
    '76561197977830137','76561197994902451','76561197996693344','76561198008816742','76561198002295348',
    '76561198182823025','76561198001483507','76561198008547848','76561198018347088','76561198055119851',
    '76561198014821181','76561198012958988','76561198021881923','76561198110772539','76561198041403773',
    '76561198075873318','76561198179203018','76561198272740044','76561198314988589','76561198298356831',
    '76561198888303335','76561199014713266','76561198435771387','76561198439776811','76561198015066798',
    
    
    '76561198069244425','76561198035677334','76561198025960084','76561198013129575','76561198014373302',
    '76561198019240186','76561198040922078','76561197997882074','76561198007508343','76561198010283178',
    '76561198042906679','76561198009688189','76561197976169768','76561198137993127','76561198172235266',
    '76561198107180896','76561198143233564','76561198102491591','76561198197966341','76561198440627935',
    '76561198197966341','76561198305892582','76561198833190282','76561198860457381','76561198452841482',



]

DATA_FILE = 'friend_data.json'
INIT_FILE = '.initialized'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteamFriendIDMonitor")

def get_profile_link(steam_id):
    """Generate Steam profile link from Steam ID"""
    return f"steamcommunity.com/profiles/{steam_id}"

async def fetch_friend_list(session, steam_id):
    """Fetch the complete friend list for a Steam account"""
    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"
    profile_link = get_profile_link(steam_id)
    
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                friends_data = data.get('friendslist', {}).get('friends', [])
                # Extract just the Steam IDs of friends
                friend_ids = [friend['steamid'] for friend in friends_data]
                return steam_id, profile_link, friend_ids
            elif resp.status == 403:
                logger.warning(f"{profile_link} is private")
                return steam_id, profile_link, None
            else:
                logger.error(f"{profile_link}: API error {resp.status}")
                return steam_id, profile_link, None
    except Exception as e:
        logger.error(f"Error fetching {profile_link}: {e}")
        return steam_id, profile_link, None

async def send_telegram_message(message):
    """Send message to Telegram, splitting if too long"""
    MAX_MESSAGE_LENGTH = 4000  # Leave some buffer under 4096 limit
    
    if len(message) <= MAX_MESSAGE_LENGTH:
        await _send_single_message(message)
    else:
        # Split message into chunks
        lines = message.split('\n')
        current_chunk = ""
        
        for line in lines:
            # If adding this line would exceed limit, send current chunk
            if len(current_chunk + line + '\n') > MAX_MESSAGE_LENGTH:
                if current_chunk:
                    await _send_single_message(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Single line is too long, truncate it
                    await _send_single_message(line[:MAX_MESSAGE_LENGTH])
            else:
                current_chunk += line + '\n'
        
        # Send remaining chunk
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
            async with session.post(url, data=payload) as resp:
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

async def check_accounts():
    """Main function to check all accounts for friend changes"""
    first_run = is_first_run()
    previous_data = load_previous_data()
    current_data = {}
    all_new_friends = []  # Collect all new friends for batched notification
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_friend_list(session, steam_id) for steam_id in STEAM_ACCOUNTS]
        results = await asyncio.gather(*tasks)

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
                logger.info(f"New friend detected: {friend_id} added to {steam_id}")
        
        # Log removed friends (no telegram notification)
        removed_friends = previous_friends - current_friends
        if removed_friends:
            for friend_id in removed_friends:
                logger.info(f"Friend removed: {friend_id} removed from {steam_id}")

    # Send batched notification for all new friends
    logger.info(f"Total new friends collected: {len(all_new_friends)}")
    logger.info(f"First run status: {first_run}")
    
    if all_new_friends and not first_run:
        if len(all_new_friends) == 1:
            msg = f"New friend: {all_new_friends[0]}"
        else:
            msg = f"New friends detected ({len(all_new_friends)}):\n\n"
            msg += "\n".join([f"• {friend_link}" for friend_link in all_new_friends])
        
        logger.info(f"Attempting to send Telegram message: {msg[:100]}...")
        await send_telegram_message(msg)
        logger.info(f"Sent batched notification for {len(all_new_friends)} new friends")
    elif all_new_friends and first_run:
        logger.info(f"New friends detected on first run (not sending notification): {len(all_new_friends)}")
    else:
        logger.info("No new friends detected in this cycle")

    # Save current data
    save_data(current_data)

    if first_run:
        # Log initial setup (no telegram messages)
        total_accounts = len(current_data)
        private_accounts = len(STEAM_ACCOUNTS) - total_accounts
        total_friends = sum(data['count'] for data in current_data.values())
        
        logger.info(f"Steam Friend ID Monitor Setup Complete")
        logger.info(f"Monitoring {total_accounts} accounts")
        logger.info(f"Total friends being tracked: {total_friends}")
        if private_accounts > 0:
            logger.info(f"{private_accounts} accounts are private")
        logger.info("Bot will now notify when specific friends are added with their Steam IDs")
    else:
        logger.info("Friend check completed")

if __name__ == '__main__':
    asyncio.run(check_accounts())

if __name__ == '__main__':
    asyncio.run(check_accounts())
