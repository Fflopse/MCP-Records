import requests
import json
import os
from tqdm import tqdm
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

keywords = ['Premium+', 'Premium', 'Bauteam', 'Spieler', 'Entwickler', 'VIP', 'Content', 'Supporter', 'Owner', 'Moderator', 'Translator']

player_data = {}
player_categories = {keyword: [] for keyword in keywords}

def fetch_player_data(player_name, log=False):
    url = f"https://api.cytooxien.de/user/{player_name}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if log: 
            logging.info(f"Fetching API data for player: {player_name}")
        
        player_data[player_name] = {
            "name": player_name,
            "rank": "None",
            "minecraft_party": {}
        }
        
        if 'playerInfo' in data and 'rank' in data['playerInfo']:
            rank_name = data['playerInfo']['rank']['name']
            if rank_name in keywords:
                player_data[player_name]["rank"] = rank_name
                player_categories[rank_name].append(player_name)
                if log: 
                    logging.info(f"Player rank: {rank_name}")
            else:
                player_data[player_name]["rank"] = rank_name
        
        if 'stats' in data and 'mp' in data['stats'] and 'global' in data['stats']['mp']:
            mp_stats = data['stats']['mp']['global']
            
            wins = mp_stats.get('wins', 0)
            games = mp_stats.get('games', 0)
            minigame_wins = mp_stats.get('minigame_wins', 0)
            minigames = mp_stats.get('minigames', 0)
            
            winrate = round((wins / games * 100), 2) if games > 0 else 0
            minigame_winrate = round((minigame_wins / minigames * 100), 2) if minigames > 0 else 0
            
            stat_mapping = {
                'Gewonnene Spiele': wins,
                'Gewonnene Minispiele': minigame_wins,
                'Gespielte Spiele': games,
                'Gespielte Minispiele': minigames,
                'Spielzeit': format_time(mp_stats.get('time', 0)),
                'Punkte': mp_stats.get('points', 0),
                'Rang': mp_stats.get('rank_points', 0),
                'Winrate %': winrate,
                'Minigame Winrate %': minigame_winrate
            }
            
            player_data[player_name]["minecraft_party"] = stat_mapping
            
            if log: 
                logging.info("Found Minecraft Party data")
                for stat_name, stat_value in stat_mapping.items():
                    logging.info(f"Scraped: {stat_name} = {stat_value}")
        else:
            if log:
                logging.warning(f"No Minecraft Party data found for {player_name}")
        
        return player_data[player_name]["rank"]
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data for {player_name}: {e}")
        player_data[player_name] = {
            "name": player_name,
            "rank": "Error",
            "minecraft_party": {}
        }
        return "Error"
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON for {player_name}: {e}")
        player_data[player_name] = {
            "name": player_name,
            "rank": "Error",
            "minecraft_party": {}
        }
        return "Error"

def format_time(milliseconds):
    if milliseconds == 0:
        return "0"
    
    seconds = milliseconds // 1000
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    
    if days > 0:
        return f"{days}d {hours % 24}h {minutes % 60}m"
    elif hours > 0:
        return f"{hours}h {minutes % 60}m"
    elif minutes > 0:
        return f"{minutes}m {seconds % 60}s"
    else:
        return f"{seconds}s"

if __name__ == "__main__":
    import helpers as h
    playerList = h.assemblePlayerList()
    
    progress_bar = tqdm(playerList, desc="Fetching Progress", unit="player")
    for player_name in progress_bar:
        last_rank = fetch_player_data(player_name, log=False)
        progress_bar.set_postfix(last_rank=last_rank, last_player=player_name)
        time.sleep(0.2)
    
    with open('player_data.json', 'w', encoding='utf-8') as f:
        json.dump(player_data, f, ensure_ascii=False, indent=4)
    
    print("Data exported to player_data.json")