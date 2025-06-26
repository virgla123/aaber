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
    '76561198016392574','76561198013881188','76561199836492106','76561198012230575','76561198005196123','76561199573094006',
    '76561199573981845','76561199573340943','76561198016954842','76561199836215463','76561198017595036','76561198008178255',
    '76561198017152156','76561198007667299','76561198006780178','76561197989423966','76561198016951209','76561199836237875',
    '76561198031290197','76561198009534162','76561199836250812','76561198008565289','76561198009862925','76561198014361836',
    '76561198009908412','76561198006467127','76561199836064571','76561198008997824','76561198017580626','76561199496365187',
    '76561199573680536','76561199573298087','76561199836643886','76561198011856806','76561198011402939','76561198010038484',
    '76561199487612972','76561199573714328','76561199573551468','76561199573416584','76561198013354511','76561199574188093',
    '76561199496074573','76561199495787230','76561199497103943','76561198008578973',
    '76561198008578973','76561198010533068','76561199573959249','76561198006062768','76561199836353839','76561199836238073',
    '76561198012000667','76561199573953205','76561199496998599','76561199835779907','76561199836941150','76561199835714035',
    '76561198015662733','76561198012727008','76561198021032471','76561198026691333','76561199266026870','76561199488078467',
    '76561199496694534','76561199488055800','76561199489203629','76561199487125232','76561199489088333','76561199496714603',
    '76561199487868994','76561199573794440','76561199573644228','76561199572962362','76561199573768485','76561199144439232',
    '76561199574784892','76561199573365283','76561199572711408','76561199573732694','76561199573862496','76561199277499283',
    '76561199497330208','76561199488518544','76561199486872940','76561199488012632','76561199496616686','76561199496238556',
    '76561199488496947',
    '76561199497135931','76561198015548342','76561198011979027','76561198018294251','76561198007169826','76561198013854404',
    '76561199835797669','76561198012630531','76561198011773927','76561199835585176','76561199836484599','76561199836616157',
    '76561198011579626','76561198006061648','76561198009152296','76561199836538185','76561198010554694','76561198016214851',
    '76561199835981349','76561199574409923','76561199573352203','76561199573375376','76561199573566227','76561199573909766',
    '76561198993755095','76561199573449635','76561199573476621','76561199573592850','76561199573362507','76561199573402162',
    '76561199573579600','76561199573751034','76561199573979213','76561199573792519','76561199573888034','76561198026898348',
    '76561199489126661','76561199488260620','76561199487314882','76561199380332744','76561199486991319','76561199355955937',
    '76561199488865230','76561199496504070','76561199496430534','76561199573666958','76561198016733599','76561199573545056',
    '76561199573626704',
    '76561199573937302','76561199573410097','76561199574133104','76561199573896225','76561199574137298','76561199574029212',
    '76561199574199421','76561199573650799','76561199572930037','76561199488627032','76561199487686992','76561199496116257',
    '76561199488128914','76561198013011126','76561199836251217','76561198011040049','76561199836463893','76561198014226001',
    '76561198005997024','76561198010336775','76561198011490554','76561198011790488','76561198011944645','76561198014221038',
    '76561198016000277','76561198010155055','76561199836973714','76561198017343972','76561199835290638','76561198005431705',
    '76561198009970256','76561198007849352','76561199835928149','76561199836477677','76561198007311915','76561199836905182',
    '76561198007067304','76561199573482721','76561199573367564','76561199572828554','76561199573187124','76561199573234455',
    '76561199573532651','76561199573483831','76561199487970760','76561199496389553','76561199573601964','76561199573629987',
    '76561199496529390','76561199497174531','76561199487857799',
    '76561199496026508','76561198014145241','76561198016855317','76561198005753412','76561198011843941','76561198005598626',
    '76561198007766613','76561198012057834','76561199836584366','76561199573112130','76561198005542453','76561199836993540',
    '76561198012596142','76561198012443637','76561198005196400','76561199836425103','76561199836121084','76561198017571997',
    '76561198009906360','76561198008342309','76561197992383333','76561199574333530','76561199495370914','76561198010670982',
    '76561199836235727','76561199836595868','76561199835793403','76561198012764220','76561198004943213','76561198011507370',
    '76561199836623819','76561198009912613','76561198011645330','76561199573352744','76561199495994444','76561199496738518',
    '76561199496907701','76561198006443045',
    '76561198006443045','76561198011166219','76561199496342547','76561199496273250','76561199495397299','76561199496695874',
    '76561199496154786','76561199835927937','76561198012181522','76561198008145037','76561199488075492','76561199487395372',
    '76561199488539400','76561199489575644','76561199310382195','76561199496651111','76561199487369299','76561199489140134',
    '76561199496629890','76561199496429133','76561199496846851','76561199488824878','76561199496825469','76561199495975116',
    '76561199487650377','76561199495816117','76561199496794618','76561199496508051','76561199489459972',
    '76561199496508051','76561199496794618','76561199489459972','76561199489774630','76561199310441949','76561199496745885',
    '76561199573773797','76561199573210567','76561199573441808','76561199574224569','76561199574005694','76561199573971888',
    '76561199573589041','76561199573869020','76561199573835820','76561199573566423','76561199573820950','76561199573829117',
    '76561199573569054','76561199573635241','76561199115152486','76561199573829902','76561199573952269','76561199573179223',
    '76561199573331720','76561199489024221','76561199496028249','76561199487203978','76561199488810816','76561199490023145',
    '76561199343768581','76561199488616610','76561199497121095','76561199496260756','76561199489460772','76561199489931345',
    '76561199488248265','76561199488330716','76561199487745240','76561199487362295','76561199496113274','76561199496434423',
    '76561199489765233','76561199489714316','76561199496497346',
    '76561199496502806','76561199487510751','76561199496497346','76561199489765233','76561199488106889','76561199496416970',
    '76561199487497538','76561199185686175','76561199573367047','76561199574095391','76561199572957833','76561199573478396',
    '76561199573234981','76561199574067723','76561199574509115','76561199572747365','76561199573458882','76561199573650929',
    '76561199573247369','76561199573309378','76561199573312098','76561199573504620','76561199573896785','76561199573375703',
    '76561199573378684','76561199573967070','76561199573790149','76561199573213824','76561199573359907','76561199186155126',
    '76561199573514884','76561199152394970','76561199573492095','76561199573778786','76561199573734788','76561199573718102',
    '76561199574002078','76561199573720655','76561199573662867','76561198990043219','76561199573040238','76561199496723661',
    '76561199487835346','76561199488199331','76561199488038205','76561199487440925','76561199496694203','76561199488608419',
    '76561199487327979','76561199488135882',
    '76561199487835346','76561199488199331','76561199487440925','76561199489745505','76561199487840570','76561199496444525',
    '76561199496229894','76561199496989854','76561199182986556','76561199496723661','76561199573802128','76561199573734358',
    '76561199573986410','76561199573380811','76561199573773381','76561199574282754','76561199573564239','76561199573523768',
    '76561199573837379','76561199573800848','76561199573583824','76561199574003192','76561199574039370','76561199573448459',
    '76561199574202926','76561199573628497','76561199572911787','76561199573227265','76561199573774228','76561199573331752',
    '76561199574108969','76561199574105671','76561199124726174','76561199573795667','76561199573472161','76561199573301571',
    '76561199496748871','76561199489871066','76561199489922840','76561199496660782','76561199496574514','76561199368674766',
    '76561199496268110','76561199496846289','76561199488060553','76561199496510564','76561199488674814','76561199192557547',
    '76561199573183917',
    '76561199574111760','76561199573585387','76561199573835655','76561199573584523','76561199192557547','76561199191145332',
    '76561199574046319','76561199573838752','76561199573822530','76561199573845987','76561199573505995','76561199573015479',
    '76561199573066754','76561199497237243','76561199496810378','76561199488735809','76561199488238783','76561199573347029',
    '76561199490240223','76561199487976369','76561199496211919','76561199573908950','76561199038044620','76561199573721428',
    '76561199573850139','76561199573777924','76561199573848980','76561199487098175','76561199380890506','76561199489422738',
    '76561199497001587','76561199573834618','76561199573214724','76561199572728933','76561199573695427','76561199573811992',
    '76561199573875522','76561199189490924','76561199573509360','76561199487756908','76561199496671591','76561199186067398',
    '76561199573382024','76561199573178014','76561199488351517','76561199188869387',

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
