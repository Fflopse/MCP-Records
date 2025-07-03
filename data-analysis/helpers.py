import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def get_username_from_uuid(uuid):
    """Get current username for a given UUID"""
    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            profile = response.json()
            return profile['name']
        else:
            return None
    except Exception as e:
        print(f"Error for UUID {uuid}: {e}")
        return None

def update_player_names(input_file, output_file, max_workers=10, delay=0.1):
    """Update player names from UUIDs and save to new file"""
    
    # Load existing data
    with open(input_file, 'r') as f:
        old_data = json.load(f)
    
    print(f"Processing {len(old_data)} players...")
    
    # Get all unique UUIDs
    unique_uuids = list(set(old_data.values()))
    print(f"Found {len(unique_uuids)} unique UUIDs")
    
    # Fetch current usernames
    uuid_to_name = {}
    
    def fetch_with_delay(uuid):
        time.sleep(delay)
        name = get_username_from_uuid(uuid)
        return uuid, name
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_uuid = {executor.submit(fetch_with_delay, uuid): uuid for uuid in unique_uuids}
        
        for i, future in enumerate(as_completed(future_to_uuid)):
            uuid, current_name = future.result()
            if current_name:
                uuid_to_name[uuid] = current_name
                print(f"Progress: {i+1}/{len(unique_uuids)} - {current_name}")
            else:
                print(f"Progress: {i+1}/{len(unique_uuids)} - Failed to get name for {uuid}")
    
    # Create updated data structure
    updated_data = {}
    name_changes = []
    
    for old_name, uuid in old_data.items():
        current_name = uuid_to_name.get(uuid)
        if current_name:
            updated_data[current_name] = uuid
            if old_name != current_name:
                name_changes.append((old_name, current_name, uuid))
        else:
            # Keep old entry if we couldn't fetch current name
            updated_data[old_name] = uuid
            print(f"Warning: Keeping old name '{old_name}' - couldn't fetch current name")
    
    # Save updated data
    with open(output_file, 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    # Print summary
    print(f"\nUpdate complete!")
    print(f"Total players: {len(updated_data)}")
    print(f"Name changes detected: {len(name_changes)}")
    print(f"Updated data saved to: {output_file}")
    
    if name_changes:
        print("\nName changes:")
        for old_name, new_name, uuid in name_changes:
            print(f"  {old_name} -> {new_name} ({uuid})")
    
    return updated_data, name_changes

def create_name_list(data, output_file):
    """Create a simple list of current player names"""
    names = sorted(data.keys())
    
    with open(output_file, 'w') as f:
        for name in names:
            f.write(f"{name}\n")
    
    print(f"Player name list saved to: {output_file}")
    return names

def assemblePlayerList():
    # Update the player data
    updated_data, changes = update_player_names(
        'player_uuids.json', # source file
        'player_uuids.json' # target file
    )
    
    # Create a simple name list
    names = create_name_list(updated_data, 'player_names.txt')
    
    print(f"\nCurrent player names ({len(names)} total):")
    for i, name in enumerate(names[:10]):  # Show first 10
        print(f"  {name}")
    if len(names) > 10:
        print(f"  ... and {len(names) - 10} more")

    return names