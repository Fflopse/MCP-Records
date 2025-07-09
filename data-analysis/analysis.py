import pandas as pd
import numpy as np
from collections import defaultdict
import os
import re 
import seaborn as sns 
import chardet
import warnings
import seaborn as sns
import matplotlib.pyplot as plt


pointMiniGames = "Sammelwahn, Schießstand, Mauerfall, Survivalgames, Skywars, Lasertag, Minengefecht, Einer im Köcher, Paintball, Spleef, Buntes Chaos, Reihenfolge, Duelle, Turmroulette" 
timeMiniGames = "Wettrennen, Parkour, Pferderennen, Drachenflucht, Replika, Blockhüpfer, Todeswürfel, Freier Fall, Elytrarennen, Waffenfolge, Minenfeld, Kletterkönig, Ampelrennen, Hoch hinaus, Frostiger Pfad, Runterpurzeln"

miniGameList = ["1-Sammelwahn",
        "2-Schießstand",
        "3-Wettrennen",
        "4-Pferderennen",
        "5-Drachenflucht",
        "6-Parkour",
        "7-Hoch Hinaus",
        "8-Blockhüpfer",
        "9-Todeswürfel",
        "10-Freier Fall",
        "11-Elytrarennen",
        "12-Waffenfolge",
        "13-Minenfeld",
        "14-Kletterkönig",
        "15-Ampelrennen",
        "16-Replika",
        "17-Mauerfall",
        "18-Survivalgames",
        "19-Skywars",
        "20-Lasertag",
        "21-Minengefecht",
        "22-OITC",
        "23-Paintball",
        "24-Spleef",
        "25-Buntes Chaos",
        "26-Reihenfolge",
        "27-Duelle",
        "28-Frotiger Pfad",
        "29-Runterpurzeln",
        "30-Turmroulette"]

inactiveMinigames = ["Paintball", "Freier Fall"]



def merge_duplicate_columns(df):
    """
    Merges columns that are duplicates following the pattern:
    - Base column (e.g., "Oasis")
    - Kill variant (e.g., "Kill Oasis") 
    - Kills variant (e.g., "Kills Oasis")
    
    Priority: Base > Kills > Kill (first non-null value wins)
    """
    df = df.copy()
    column_groups = defaultdict(list)
    
    for col in df.columns:
        if col.startswith("Kill "):
            base_name = col[5:]
            column_groups[base_name].append(("kill", col))
        elif col.startswith("Kills "):
            base_name = col[6:]
            column_groups[base_name].append(("kills", col))
        else:
            column_groups[col].append(("base", col))
    
    columns_to_drop = []
    
    for base_name, variants in column_groups.items():
        if len(variants) > 1:
            base_col = None
            kills_col = None
            kill_col = None
            
            for variant_type, col_name in variants:
                if variant_type == "base":
                    base_col = col_name
                elif variant_type == "kills":
                    kills_col = col_name
                elif variant_type == "kill":
                    kill_col = col_name
            
            target_col = base_col or kills_col or kill_col
            
            for variant_type, col_name in variants:
                if col_name != target_col:
                    df[col_name] = df[col_name].replace(0, np.nan)
            
            if base_col and base_col != target_col:
                df[base_col] = df[base_col].replace(0, np.nan)
            
            merge_order = []
            if base_col: merge_order.append(base_col)
            if kills_col: merge_order.append(kills_col)  
            if kill_col: merge_order.append(kill_col)
            
            if len(merge_order) > 1:
                for i in range(1, len(merge_order)):
                    df[merge_order[0]] = df[merge_order[0]].fillna(df[merge_order[i]])
                    columns_to_drop.append(merge_order[i])
    
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')
    return df

import os

def remove_kein_rekord_lines(directory_path="in-new/"):
    if not os.path.exists(directory_path):
        print(f"Directory '{directory_path}' not found.")
        return
    
    txt_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"No .txt files found in '{directory_path}'")
        return
    
    processed_count = 0
    
    for filename in txt_files:
        file_path = os.path.join(directory_path, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            original_count = len(lines)
            filtered_lines = [line for line in lines if '' not in line]
            removed_count = original_count - len(filtered_lines)
            
            if removed_count > 0:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(filtered_lines)
                print(f"Processed '{filename}': removed {removed_count} line(s)")
                processed_count += 1
            else:
                print(f"No changes needed for '{filename}'")
                
        except Exception as e:
            print(f"Error processing '{filename}': {e}")
    
    print(f"\nCompleted processing {len(txt_files)} file(s), {processed_count} file(s) modified.")

def getPlayerPaths():
    file_list = os.listdir('in-new')
    return file_list

def read_file(file, enc='auto'):

    with open('in-new/' + file, 'rb') as f:
        raw_data = f.read()
    
    # Detect the encoding
    if enc == 'auto':
        # detected = chardet.detect(raw_data)
        encoding = 'utf-8'
    #encoding = 'iso-8859-2'
    encoding = 'utf-8'

    # debug print(f"Detected encoding for {file}: {encoding}")
    
    # Now read the file with the detected encoding
    with open('in-new/' + file, 'r', encoding=encoding) as f:
        data = f.read().replace('TooltipEvent, ', '')
    
    return data

def getRecordData(playerPath, minigame, enc='auto'):
    data = read_file(playerPath, enc=enc).split('\n')
    for line in data: 
        if minigame in line: 
            minigameData = line
            minigameData = minigameData.replace(minigame, '').strip()
            return minigameData  # return the data instead of printing it

def create_dataframe(input_string, minigame):

    # Define regular expression pattern to match map names and times
    pattern = r'(\w+\s?\w+)\s*:\s*(?:(\d+)\s*min\s*)?(?:(\d+)\s*s\s*)?(\d+)\s*ms'

    # Find all matches in the input string
    try: matches = re.findall(pattern, input_string)
    except: matches = None

    # Initialize data dictionary to store map names and times
    data = {}

    # Iterate over matches and populate data dictionary
    if matches: 
        for match in matches:
            map_name = match[0]
            minutes = int(match[1] or 0)
            seconds = int(match[2] or 0) + int(match[3]) / 1000
            time_seconds = minutes * 60 + seconds
            data[map_name] = time_seconds
    else: return pd.DataFrame()

    # Create DataFrame from data dictionary
    df = pd.DataFrame(data, index=[0])


    return df


def createPointDataframe(input_string, minigame):
    # Define regular expression pattern to match map names and times
    pattern = r'(\w+\s?\w+)\s*:\s*(\d+)'

    # Find all matches in the input string
    matches = re.findall(pattern, input_string)

    # Initialize data dictionary to store map names and times
    data = {}

    # Iterate over matches and populate data dictionary
    for match in matches:
        map_name = match[0]
        time_value = int(match[1])
        data[map_name] = time_value

    # Create DataFrame from data dictionary
    df = pd.DataFrame(data, index=[0])
    return df.fillna(0)


paths = getPlayerPaths()

def getRecordsDataframe(minigame='Wettrennen', save=False, log=False, html=False, encoding='auto'):

    if minigame in inactiveMinigames:
        return None
    
    outDf = pd.DataFrame()

    if log:
        print(f'processing {minigame}...')

    if minigame in pointMiniGames: 
        pass
    elif minigame in timeMiniGames:
        pass
    else: 
        ValueError('Not a valid minigame name')

    for i in paths:
        if minigame in timeMiniGames:
            df = create_dataframe(getRecordData(playerPath=i, minigame=minigame, enc='auto'), minigame)
        if minigame in pointMiniGames:
            try: 
                df = createPointDataframe(getRecordData(playerPath=i, minigame=minigame, enc='auto'), minigame)
                df.fillna(0, inplace=True)
            except: 
                continue

        if df is not None:  
            df.index = [i.replace('.txt', '')]
            outDf = pd.concat([outDf, df])

    outPath = 'out/' + minigame + '.json'

    '''
        Minigame Specific changes to the df
    '''
    with pd.option_context('mode.chained_assignment', None):
        try:
            if ("Replika" in minigame): 

                replikaDf = outDf 

                # fillNa columns without "ms" with values from "ms", e.g. ms Arrow -> Arrow, then drop "ms" columns

                try:
                    replikaDf["Arrow"] = replikaDf["Arrow"].fillna(replikaDf["ms Arrow"])
                    replikaDf["Cow"] = replikaDf["Cow"].fillna(replikaDf["ms Cow"])
                    replikaDf["Deadpool"] = replikaDf["Deadpool"].fillna(replikaDf["ms Deadpool"])
                    replikaDf["Doge"] = replikaDf["Doge"].fillna(replikaDf["ms Doge"])
                    replikaDf["Sonic"] = replikaDf["Sonic"].fillna(replikaDf["ms Sonic"])

                    replikaDf.drop(columns=["ms Arrow", "ms Cow", "ms Deadpool", "ms Doge", "ms Sonic"], inplace=True)
                except: print("Warning, >ms< columns not found in ReplikaDf")

                replikaDf.fillna(25, inplace=True) # assigning a value to a never-played-before pattern, 17 perturbs worse player order and alt account stats lol, 27 is probably too much, difficult to choose an appropriate value here
                row_sums = replikaDf.sum(axis=1)
                
                # Append the sum as a new column
                replikaDf['Sum'] = row_sums

                # Re-indexing
                replikaDf = replikaDf.reindex(sorted(replikaDf.columns), axis=1)
            
                # Move 'Sum' column to the first position
                cols = replikaDf.columns.tolist()
                cols = ['Sum'] + [col for col in cols if col != 'Sum']
                replikaDf = replikaDf[cols]

                # replace 25 values again with None
                replikaDf = replikaDf.replace(25, np.nan)

                # replikaDf = replikaDf.reindex(sorted(replikaDf.columns), axis=1)


                # Removing player data with too many NaNs (players that haven't played most of the patterns)
                # replikaDf = replikaDf.drop(columns=["Ritokii", "Feinberg", "Sebi1801"])

                outDf = replikaDf

            if ("Sammelwahn" in minigame):

                row_sums = outDf.sum(axis=1)

                # Append the sum as a new column
                outDf['Sum'] = row_sums

                # Re-indexing
                outDf = outDf.reindex(sorted(outDf.columns), axis=1)

                # Move 'Sum' column to the first position
                cols = outDf.columns.tolist()
                cols = ['Sum'] + [col.lstrip() for col in cols if col != 'Sum']
                outDf = outDf[cols]

                # remove "Punkte" from all columns
                outDf.columns = outDf.columns.str.replace('Punkte', '')
            
            if ("Buntes" in minigame):
                print(outDf.columns)

            if ("Lasertag" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Einer im Köcher" in minigame):
                outDf = merge_duplicate_columns(outDf)
                
            if ("Paintball" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Skywars" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Survivalgames" in minigame and True):
                outDf = merge_duplicate_columns(outDf)

            if ("Minengefecht" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Mauerfall" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Schie" in minigame):
                outDf["Punkte City"] = outDf["Punkte City"].replace(0, np.nan)
                outDf["City"] = outDf["City"].replace(0, np.nan)

                outDf["temp1"] = outDf["City"].fillna(outDf["Punkte City"])
                try: outDf.drop(columns=["City", "Punkte City"], inplace=True)
                except: pass

                outDf["City"] = outDf["temp1"]

                outDf["Punkte Jungle"] = outDf["Punkte Jungle"].replace(0, np.nan)

                outDf["temp1"] = outDf["Punkte Jungle"]
                try: outDf.drop(columns=["Punkte Jungle"], inplace=True)
                except: pass

                outDf["Jungle"] = outDf["temp1"]

                outDf.drop(columns=["temp1"], inplace=True)
                
            if ("Frostiger" in minigame): 
                # remove values bigger than 100 with nan
                outDf = outDf.where(outDf < 100, np.nan)

            if ("Duel" in minigame): 
                outDf = outDf.where(outDf > 10, 0.0)

            if ("Einer im Köcher" in minigame):
                outDf = merge_duplicate_columns(outDf)

            if ("Buntes" in minigame):
                
                outDf = outDf.fillna(0)
                try: 
                    outDf['temp1'] = outDf["Runden Cyberpunk"].fillna(outDf["Cyberpunk"])
                    outDf.drop(columns=["Runden Cyberpunk", "Cyberpunk"], inplace=True)

                    outDf['Cyberpunk'] = outDf['temp1']

                    outDf.drop(columns=["temp1"], inplace=True)
                except: pass

            if ("Pferd" in minigame):
                outDf["s Arena"] = outDf["s Arena"].replace(0, np.nan)
                outDf["Wario's Arena"] = outDf["s Arena"]

                outDf.drop(columns=["s Arena"], inplace=True)


            # Sorting columns alphabetically for any outDf except if minigame == "Replika" (sum column)
            
            if ("Replika" not in minigame):
                if ("Sammelwahn" not in minigame):
                    outDf = outDf.reindex(sorted(outDf.columns), axis=1)
        except: pass

    '''
        debugging options and html export for figure generation
    '''
        
    if save: 
        if "Replika" in minigame: 
            json_df = outDf.iloc[:, 1:]
            json_df.T.to_json(outPath)
        
        else: outDf.T.to_json(outPath) 


    if html: 
        log = False 
        html_table = ""
        if ("Drache" in minigame) or ("Mini" in minigame) or ("Köcher" in minigame) or ("Lasertag" in minigame) or ("Minengef" in minigame) or ("Paint" in minigame) or ("Reihenf" in minigame) or ("Sammel" in minigame) or ("Schießs" in minigame) or ("Spleef" in minigame) or ("Mauerfall" in minigame): 
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('<td>NaN</td>', '<td>0</td>').replace('.0</td>', '</td>').replace('Tötungen Asia', 'Asia').replace('Tötungen', '').replace('Punkte', '')
        elif ("Pferde" in minigame):
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('>9', '>09').replace('>8', '>08').replace('>7', '>07').replace('>6', '>06').replace('>5', '>05').replace('>4', '>04').replace('s Arena', "Wario's Arena").replace('>Cheep B', ">Cheep Cheep B")
        elif ("Replika" in minigame): 
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('>9.', '>09.').replace('>8.', '>08.').replace('>7.', '>07.').replace('>6.', '>06.').replace('>5.', '>05.').replace('>4.', '>04.').replace('>3.', '>03.').replace('>ms ','>').replace('>30.000','>None')
        elif ("Wettrennen" in minigame):
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('Punkte', '').replace('Runden', '').replace('Blossom', 'Cherry Blossom').replace('>3', '>03').replace('>4', '>04').replace('>5', '>05').replace('>6', '>06').replace('>7', '>07').replace('>8', '>08').replace('>9', '>09')
        elif ("Elytra" in minigame):
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('Punkte', '').replace('Runden', '').replace('>9', '>09').replace('>8', '>08').replace('>7', '>07').replace('>6', '>06').replace('>5', '>05').replace('>4', '>04').replace('>3', '>03')
        else: 
            html_table = (outDf.to_html()).replace('\n', '').replace('<table border="1" class="dataframe">', '').replace('Punkte', '').replace('Runden', '').replace('Blossom', 'Cherry Blossom')
        
        print(html_table)

    if log: 
        print(f'{minigame} processed and saved to {outPath}')

    if html == False: 
        return outDf
    
import json

def export_records_json(minigames):
    try:
        all_records = []
        for minigame in sorted(minigames):
            if minigame not in inactiveMinigames:
                records = getRecordsDataframe(minigame=minigame, save=False, log=False, encoding='auto'
                                            )
                
                # Print column names for debugging
                print(f"Columns for {minigame}: {records.columns.tolist()}")
                
                for player_name, row in records.iterrows():
                    record = {
                        "name": player_name,
                        "minigame": minigame,
                        "scores": {}
                    }
                    
                    # Assuming all non-index columns are map names
                    for map_name in records.columns:
                        score = row[map_name]
                        if pd.notna(score):  # Only include non-null scores
                            record["scores"][map_name] = score
                    
                    # Calculate and add the best score
                    if record["scores"]:
                        record["best_score"] = max(record["scores"].values())
                    
                    all_records.append(record)
            
            return json.dumps(all_records, indent=2)
    except: 
        print("Error in export_records_json for minigame: " + minigame)
        return None

def jsonExport(debug=False):

    minigames = (pointMiniGames + ', ' + timeMiniGames).split(', ')

    if debug: print(f"processing {minigames}")
    json_data = export_records_json(minigames)

    if debug: print("json_data has a length of: " + str(len(json_data)))

    # Save as separate file
    with open('records_data.json', 'w') as f:
        if json_data is not None:
            f.write(json_data)
        else: pass

    print("Data exported successfully to records_data.json")


def assembleHTML():

    # HTML assembly #

    frontWrapperList = []
    x = 0
    endWrapper = "</table> </div>"

    for i in sorted((pointMiniGames + ', ' + timeMiniGames).split(', ')):
        x = x + 1
        strX = str(x)
        frontWrapperList.append('<!-- Table: ' + i + ' --> <div id="table' + strX + '" style="display:none;"> <table id="dataframe' + strX + '" class="display nowrap">')

    print('<div class="table-container">')
    x = 0
    for i in sorted((pointMiniGames + ', ' + timeMiniGames).split(', ')):
        print(frontWrapperList[x])
        getRecordsDataframe(minigame=i, save=True, log=False, html=True, encoding="auto")
        print(endWrapper)
        x = x + 1
    print('</div>')


def check_file_encodings(directory='in-new'):
    """
    Check the encoding of all files in the specified directory.
    Returns a DataFrame with file information and detailed encoding analysis.
    """
    # Store results
    results = []
    
    # Get list of files
    files = os.listdir(directory)
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        
        # Read file in binary mode
        with open(filepath, 'rb') as f:
            raw_data = f.read()
            
        # Detect encoding
        detection = chardet.detect(raw_data)
        
        # Try to decode with UTF-8
        is_utf8 = True
        try:
            raw_data.decode('utf-8')
        except UnicodeDecodeError:
            is_utf8 = False
            
        # Get file size
        file_size = os.path.getsize(filepath)
            
        results.append({
            'filename': filename,
            'detected_encoding': detection['encoding'],
            'confidence': detection['confidence'],
            'is_utf8': is_utf8,
            'file_size': file_size
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Add summary statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"Total files: {len(files)}")
    print(f"Files that are UTF-8: {df['is_utf8'].sum()}")
    print(f"Files that are not UTF-8: {len(files) - df['is_utf8'].sum()}")
    print("\nDetected encodings distribution:")
    print(df['detected_encoding'].value_counts())
    
    # Show problematic files
    print("\nFiles that are not UTF-8:")
    problematic_files = df[~df['is_utf8']]
    if len(problematic_files) > 0:
        print(problematic_files[['filename', 'detected_encoding', 'confidence']])
    else:
        print("None found")
        
    return df


import json
import pandas as pd
import os

def load_existing_uuids(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_uuids(uuids, file_path):
    with open(file_path, 'w') as f:
        json.dump(uuids, f, indent=2)

def export_uuids(minigames, output_file):
    existing_uuids = load_existing_uuids(output_file)
    new_players = set()

    for minigame in sorted(minigames):
        if minigame not in inactiveMinigames:
            records = getRecordsDataframe(minigame=minigame, save=False, log=False)
            
            for player_name in records.index:
                if player_name not in existing_uuids:
                    new_players.add(player_name)

    if new_players:
        print("New players found without UUIDs:")
        for player in new_players:
            print(player)
        print("\nPlease enter UUIDs for these players (or press Enter to skip):")
        for player in new_players:
            uuid = input(f"{player}: ").strip()
            if uuid:
                existing_uuids[player] = uuid

    save_uuids(existing_uuids, output_file)
    print(f"UUIDs exported successfully to {output_file}")

def export_records_json(minigames, records_file):
    all_records = []
    for minigame in sorted(minigames):
        records = getRecordsDataframe(minigame=minigame, save=False, log=False)

        if records is None: continue
        
        for player_name, row in records.iterrows():
            record = {
                "name": player_name,
                "minigame": minigame,
                "scores": {}
            }
            
            for map_name in records.columns:
                score = row[map_name]
                if pd.notna(score):  # Only include non NaN scores
                    record["scores"][map_name] = score.item()
            
            if record["scores"]:
                record["best_score"] = max(record["scores"].values())
            
            all_records.append(record)
    
    with open(records_file, 'w') as f:
        json.dump(all_records, f, indent=2)

    print(f"Records exported successfully to {records_file}")

def exportUUIDsAndRecords():
    minigames = (pointMiniGames + ', ' + timeMiniGames).split(', ')
    export_uuids(minigames, 'player_uuids.json')
    export_records_json(minigames, 'records_data.json')

def generateSwarmPlot(save=False):
    sns.set_theme(style="whitegrid", palette="muted")

    # List of minigames to plot
    minigames = sorted((pointMiniGames + ', ' + timeMiniGames).split(', '))  # Add more minigames as needed

    # remove "Reihenfolge" from the list
    minigames.remove("Reihenfolge")

    fig, ax = plt.subplots(ncols=9, nrows=3, figsize=[20, 10])

    # Flatten the axes array to iterate over it easily
    ax = ax.flatten()

    for i, minigame in enumerate(minigames):
        data = getRecordsDataframe(minigame=minigame)
        if minigame in "Replika, Sammelwahn": 
            data = data.drop(columns=['Sum'])
        if i == 27: break 
        sns.stripplot(data=data, ax=ax[i])
        ax[i].set_title(f"{minigame}")
        ax[i].set_ylabel("")

        # Angle x-labels by 45 degrees
        ax[i].set_xticklabels(ax[i].get_xticklabels(), rotation=45, ha='right')

        # Hide overlapping x-labels
        plt.setp(ax[i].get_xticklabels(), visible=False)
        for label in ax[i].get_xticklabels():
            label.set_visible(False)
            if label.get_text() == '':
                continue
            if ax[i].xaxis.get_major_ticks()[-1].label1.get_window_extent().bounds[2] > ax[i].get_xlim()[1]:
                label.set_visible(False)
            elif label.get_window_extent().bounds[1] < 0:
                label.set_visible(False)

    # Hide any remaining empty subplots
    for i in range(len(minigames), len(ax)):
        ax[i].axis('off')

    # createSmallSwarmPlots()

    plt.tight_layout()
    plt.show()

    if save: plt.savefig('out/allSwarm.png')

def generateReplicaBoxplot(save=False):
    # Get the DataFrame for the minigame
    data = getRecordsDataframe(minigame="Replika")

    # Drop columns "ms Cow" and "ms Sonic"
    data = data.drop(columns=["Sum"])
    replData = data 

    # Calculate mean values for each category
    mean_values = data.mean()

    # Sort categories based on mean values
    sorted_categories = mean_values.sort_values().index

    # Reindex the DataFrame using the sorted category order
    data_sorted = data.reindex(columns=sorted_categories)

    # Create the boxplot
    fig, ax = plt.subplots(1, 1, figsize=[20, 10])
    sns.boxplot(data=data_sorted)

    # Rotate x-axis labels by 90 degrees and align them to the right
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')

    plt.title("Replika Record Distribution by Map")
    plt.ylabel("time [s]")
    plt.show()

    if save: plt.savefig('out/replicaSwarm.png')



    # PLOT 2
    data = getRecordsDataframe(minigame="Replika")

    # Drop columns "ms Cow" and "ms Sonic"
    data = data.drop(columns=['Sum'])

    # Calculate mean values for each category
    mean_values = data.mean()

    # Sort categories based on mean values
    sorted_categories = mean_values.sort_values().index

    # Reindex the DataFrame using the sorted category order
    data_sorted = data.reindex(columns=sorted_categories)

    # Create the boxplot
    fig, ax = plt.subplots(1, 1, figsize=[20, 10])
    sns.stripplot(data=data_sorted)

    # Rotate x-axis labels by 90 degrees and align them to the right
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')

    plt.title("Replika Record Distribution by Map")
    plt.ylabel("time [s]")
    plt.show()

    if save: plt.savefig('out/replicaSwarm2.png')


