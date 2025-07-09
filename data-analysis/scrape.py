import os
import json
import time
import requests
import keyboard
import pyautogui
from tqdm import trange
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional


class CoordinateManager:
    """Manages coordinate positions for different resolutions"""
    
    def __init__(self):
        self._4k_x = [1842, 2274, 2274, 1842, 1842, 2274]
        self._4k_y = [1155, 1155, 1209, 1209, 1260, 1260]
        
        self._2k_x = [921, 1137, 1137, 921, 921, 1137]
        self._2k_y = [int(i) / 2 for i in self._4k_y]
        
        self.fast_x = [920, 952, 992, 1032, 1062, 1102, 1132, 1132, 1102, 1062, 1032, 992, 952, 920, 920, 952, 992, 1032, 1062, 1102, 1132, 1132, 992, 952, 920]
        self.fast_y = [507, 507, 507, 507, 507, 507, 507, 550, 550, 550, 550, 550, 550, 550, 585, 585, 585, 585, 585, 585, 585, 623, 623, 623, 623]
        
        self.scale_factor_x = 1920 / 2560
        self.scale_factor_y = 1080 / 1440
        
        self._1080p_x = [int(x * self.scale_factor_x) for x in self._2k_x]
        self._1080p_y = [int(y * self.scale_factor_y) for y in self._2k_y]
    
    def get_coordinates(self, resolution: str = "2k", fast: bool = False, extended: bool = False) -> List[Tuple[int, int]]:
        """Get coordinate tuples for specified resolution and mode"""
        if fast:
            return list(zip(self.fast_x, self.fast_y))
        
        if resolution == "4k":
            base_coords = list(zip(self._4k_x, self._4k_y))
        elif resolution == "1080p":
            base_coords = list(zip(self._1080p_x, self._1080p_y))
        else:  # 2k default
            base_coords = list(zip(self._2k_x, self._2k_y))
        
        if extended:
            return self._create_extended_positions(base_coords)
        
        return base_coords
    
    def _create_extended_positions(self, coords: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Create extended list with interpolated values"""
        extended = []
        for i in range(len(coords) - 1):
            extended.append(coords[i])
            midpoint = (
                (coords[i][0] + coords[i+1][0]) // 2,
                (coords[i][1] + coords[i+1][1]) // 2
            )
            extended.append(midpoint)
        return extended


class UUIDManager:
    """Handles UUID fetching and management"""
    
    @staticmethod
    def get_uuid_from_username(username: str) -> Optional[str]:
        """Get UUID for a given username"""
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                profile = response.json()
                return profile['id']
            return None
        except Exception as e:
            print(f"Error for username {username}: {e}")
            return None
    
    @staticmethod
    def add_uuids_from_names(names_list, output_file: Optional[str] = None, max_workers: int = 10, delay: float = 0.1):
        """Add UUIDs for a list of usernames"""
        if isinstance(names_list, str):
            with open(names_list, 'r') as f:
                names = [line.strip() for line in f if line.strip()]
        else:
            names = names_list
        
        print(f"Processing {len(names)} usernames...")
        
        name_to_uuid = {}
        failed_names = []
        
        def fetch_with_delay(username):
            time.sleep(delay)
            uuid = UUIDManager.get_uuid_from_username(username)
            return username, uuid
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {executor.submit(fetch_with_delay, name): name for name in names}
            
            for i, future in enumerate(as_completed(future_to_name)):
                username, uuid = future.result()
                if uuid:
                    name_to_uuid[username] = uuid
                    print(f"Progress: {i+1}/{len(names)} - {username}: {uuid}")
                else:
                    failed_names.append(username)
                    print(f"Progress: {i+1}/{len(names)} - Failed to get UUID for {username}")
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(name_to_uuid, f, indent=2)
            print(f"UUID data saved to: {output_file}")
        
        print(f"\nProcess complete!")
        print(f"Successful: {len(name_to_uuid)}")
        print(f"Failed: {len(failed_names)}")
        
        if failed_names:
            print(f"Failed usernames: {', '.join(failed_names)}")
        
        return name_to_uuid, failed_names


class PlayerManager:
    """Manages player list operations"""
    
    @staticmethod
    def fetch_player_data(player: str) -> Dict[str, Any]:
        """Fetch player data from the API"""
        url = f"https://api.cytooxien.de/user/{player}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data for {player}: {e}")
            return None
    
    @staticmethod
    def is_player_active(player_data: Dict[str, Any]) -> bool:
        """Check if player is active based on mp monthly time > 100"""
        if not player_data:
            return False
        
        try:
            mp_monthly_time = player_data['stats']['mp']['monthly']['time']
            return mp_monthly_time > 100
        except (KeyError, TypeError):
            print(f"Missing MP data for player, considering inactive")
            return False
    
    @staticmethod
    def filter_active_players(player_list: List[str]) -> List[str]:
        """Filter playerList to keep only active players"""
        active_players = []
        
        for player in player_list:
            print(f"Checking player: {player}")
            player_data = PlayerManager.fetch_player_data(player)
            
            if PlayerManager.is_player_active(player_data):
                active_players.append(player)
                mp_time = player_data['stats']['mp']['monthly']['time']
                print(f"  ✓ Active (MP monthly time: {mp_time})")
            else:
                print(f"  ✗ Inactive (removing from list)")
        
        return active_players
    
    @staticmethod
    def process_player_list(player_list: List[str], consider_progress: bool = True) -> List[str]:
        """Process and filter player list based on desktop files and activity"""
        if consider_progress:
            desktop_path = os.path.expanduser("~/Desktop")
            desktop_files = os.listdir(desktop_path)
            
            txt_files = [f[:-4] for f in desktop_files if f.endswith(".txt")]
            
            for file in txt_files:
                try:
                    player_list.remove(file)
                except ValueError:
                    pass
            
            player_list = list(dict.fromkeys(player_list))
            
            exclusions = ["log", "itemTooltipExport"]
            for exclusion in exclusions:
                try:
                    player_list.remove(exclusion)
                except ValueError:
                    pass
        
        print(f"playerList contains {len(player_list)} unique names")
        return player_list


class RecordScraper:
    """Main scraping functionality"""
    
    def __init__(self):
        self.coord_manager = CoordinateManager()
        self.desktop_path = os.path.expanduser("~/Desktop")
    
    def scrape(self, player_list: List[str], resolution: str = "2k", fast: bool = False, 
               extended: bool = False, dur: Optional[float] = None):
        """Scrape records for each player in playerList"""
        
        desktop_files = os.listdir(self.desktop_path)
        coords = self.coord_manager.get_coordinates(resolution, fast, extended)
        
        duration = 0.7 if not fast else 0.05
        if dur is not None:
            duration = float(dur)
        
        sleep_time = duration if fast or dur is not None else 0.05
        
        for i, player in enumerate(player_list):
            if sorted(player_list) == sorted(desktop_files):
                print("All records have been scraped.")
                break
            
            with trange(len(player_list), desc="Processing players", position=0) as t:
                t.update(i)
                
                pyautogui.press("t")
                pyautogui.sleep(0.2)
                
                command = f"/rekorde {player}"
                pyautogui.sleep(0.2)
                keyboard.write(command)
                pyautogui.sleep(0.2)
                pyautogui.press("enter")
                pyautogui.sleep(0.15)
                
                pyautogui.moveTo(x=500, y=500, duration=0.002)
                
                for coord in coords:
                    pyautogui.moveTo(x=coord[0], y=coord[1], duration=duration)
                    pyautogui.sleep(sleep_time)
                
                pyautogui.press("e")
                pyautogui.sleep(0.2)
                
                self._rename_file(player)
    
    def _rename_file(self, player: str):
        """Rename the exported file to player name"""
        new_filename = f"{player}.txt"
        old_filepath = os.path.join(self.desktop_path, "ItemTooltipExport.txt")
        new_filepath = os.path.join(self.desktop_path, new_filename)
        
        try:
            os.rename(old_filepath, new_filepath)
        except Exception:
            print(f"Error renaming file for {player}.")
    
    def verify_desktop(self, player_list: List[str], debug: bool = False):
        """Verify line count for each scraped file"""
        error_count = 0
        
        for player in player_list:
            try:
                filepath = os.path.join(self.desktop_path, f"{player}.txt")
                with open(filepath, "r") as file:
                    lines = file.readlines()
                    if debug:
                        print(f"{player} has {len(lines)} lines.")
                    elif len(lines) != 24:
                        print(f"{player} has {len(lines)} lines.")
                        error_count += 1
            except FileNotFoundError:
                print(f"{player} has no file.")
                error_count += 1
        
        print(f"All files checked. {error_count} files had issues.")
    
    def clear_temp_files(self):
        """Clear temporary files from desktop"""
        temp_files = ["ItemTooltipExport.txt", "log.txt"]
        
        for temp_file in temp_files:
            try:
                os.remove(os.path.join(self.desktop_path, temp_file))
            except FileNotFoundError:
                pass


def main():
    """Example usage"""
    test_names = ["Proofreader", "CuzImKnxck", "JustAnyy", "qMika", "schwarzekater"]
    
    uuid_manager = UUIDManager()
    result, failed = uuid_manager.add_uuids_from_names(test_names, 'player_uuids_fresh.json')
    
    print(f"\nResults:")
    for name, uuid in result.items():
        print(f"  {name}: {uuid}")


if __name__ == "__main__":
    main()