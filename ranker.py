from flask import session
from flask_socketio import SocketIO, emit
from datetime import datetime
from daypart import Daypart
from bq.sqls import *
import pandas as pd
import numpy as np
import pulp
from pulp import GLPK_CMD, LpAffineExpression
import math
import re

# Mapping dictionary to find max number of feasable daypart buys
day_map = {
    'M': 1, 'T': 2, 'W': 3, 'Th': 4, 'F': 5, 'Sa': 6, 'Su': 7
}

# Network-specific VA impression discounts (%)
# Applies a discount to VideoAmp impressions for specified networks
network_va_discounts = {

    'a&e': 30,
    'abc': 30,
    'amc': 30,
    'adult swim': 30,
    'american heroes channel': 30,
    'animal planet': 30,
    'bbca': 30,
    'bet': 30,
    'bet her': 30,
    'bravo': 30,
    'cbs': 30,
    'cleo tv': 30,
    'cmt': 30,
    'cnn': 30,
    'comedy': 30,
    'cooking': 30,
    'destination america': 30,
    'discovery': 30,
    'discovery family': 30,
    'discovery life': 30,
    'discovery en español': 30,
    'e!': 30,
    'espn': 30,
    'fx': 30,
    'fxm': 30,
    'fxx': 30,
    'fyi': 30,
    'food': 30,
    'fox business': 30,
    'fox news': 30,
    'fox sports 1': 30,
    'fox sports 2': 30,
    'freeform': 30,
    'golf channel': 30,
    'gac': 30,
    'galavision': 30,
    'hgtv': 30,
    'hln': 30,
    'hallmark': 30,
    'hallmark drama': 30,
    'hmm': 30,
    'heroes & icons': 30,
    'history': 30,
    'id': 30,
    'ifc': 30,
    'lmn': 30,
    'lifetime': 30,
    'logo tv': 30,
    'mlb network': 30,
    'ms now': 0,
    'mtv': 30,
    'mtv2': 30,
    'magnolia network': 30,
    'metv': 30,
    'discovery turbo': 30,
    'nbc': 30,
    'nfl network': 30,
    'ngw': 30,
    'nat geo': 30,
    'nick jr.': 30,
    'nick at nite': 30,
    'nickelodeon': 30,
    'own': 30,
    'outdoor channel': 30,
    'oxygen': 30,
    'paramount': 30,
    'pop': 30,
    'reelz': 30,
    'science': 30,
    'smithsonian channel': 30,
    'sundance': 30,
    'syfy': 30,
    'tbs': 30,
    'tlc': 30,
    'tnt': 30,
    'tv land': 30,
    'tv one': 30,
    'teen nick': 30,
    'telemundo': 30,
    'travel': 30,
    'trutv': 30,
    'tudn': 30,
    'up': 30,
    'univision': 30,
    'unimas': 30,
    'universo': 30,
    'usa': 30,
    'vh1': 30,
    'we': 30

}

guaranteed_minimums = {
    "A&E": 175000,
    "ABC": 200000,
    "AMC": 85000,
    "Adult Swim": 200000,
    "American Heroes Channel": 25000,
    "Animal Planet": 75000,
    "BBCA": 85000,
    "BET": 75000,
    "BET Her": 25000,
    "Bravo": 100000,
    "CBS": 425000,
    "CLEO TV": 25000,
    "CMT": 50000,
    "CNN": 100000,
    "Comedy": 100000,
    "Cooking": 75000,
    "Destination America": 25000,
    "Discovery": 175000,
    "Discovery Family": 25000,
    "Discovery Life": 25000,
    "Discovery en Español": 25000,
    "E!": 100000,
    "ESPN": 500000,
    "FX": 150000,
    "FXM": 50000,
    "FXX": 100000,
    "FYI": 150000,
    "Food": 200000,
    "Fox Business": 75000,
    "Fox News": 150000,
    "Fox Sports 1": 75000,
    "Fox Sports 2": 50000,
    "Freeform": 150000,
    "Golf Channel": 150000,
    "GAC": 25000,
    "HGTV": 200000,
    "HLN": 50000,
    "Hallmark": 200000,
    "Hallmark Drama": 100000,
    "Hallmark Mystery": 100000,
    "Heroes & Icons": 50000,
    "History": 175000,
    "ID": 125000,
    "IFC": 50000,
    "LMN": 150000,
    "Lifetime": 175000,
    "Logo TV": 50000,
    "MLB Network": 75000,
    "MS Now": 125000,
    "MTV": 100000,
    "MTV2": 50000,
    "Magnolia Network": 75000,
    "MeTV": 150000,
    "Discovery Turbo": 75000,
    "NBC": 350000,
    "NFL Network": 150000,
    "NGW": 50000,
    "Nat Geo": 75000,
    "Nick Jr.": 75000,
    "Nick at Nite": 150000,
    "Nickelodeon": 150000,
    "OWN": 100000,
    "Outdoor Channel": 25000,
    "Oxygen": 75000,
    "Paramount": 100000,
    "Pop": 100000,
    "Reelz": 100000,
    "Science": 50000,
    "Smithsonian Channel": 50000,
    "Sundance": 50000,
    "SyFy": 100000,
    "TBS": 200000,
    "TLC": 125000,
    "TNT": 200000,
    "TV Land": 100000,
    "TV One": 75000,
    "Teen Nick": 75000,
    "Telemundo": 150000,
    "Travel": 100000,
    "TruTV": 200000,
    "UNIVERSO": 50000,
    "USA": 150000,
    "VH1": 100000,
    "WE": 85000,
}

# Network maximums - enforced whenever a network is used
# Network maximums - enforced whenever a network is used
guaranteed_maximums = {
    "A&E": 350000,
    "ABC": 400000,
    "AMC": 170000,
    "Adult Swim": 400000,
    "American Heroes Channel": 50000,
    "Animal Planet": 150000,
    "BBCA": 170000,
    "BET": 150000,
    "BET Her": 50000,
    "Bravo": 200000,
    "CBS": 850000,
    "CLEO TV": 50000,
    "CMT": 100000,
    "CNN": 200000,
    "Comedy ": 200000,
    "Cooking": 150000,
    "Destination America": 50000,
    "Discovery": 350000,
    "Discovery Family": 50000,
    "Discovery Life": 50000,
    "Discovery en Español": 50000,
    "E!": 200000,
    "ESPN": 1000000,
    "FX": 300000,
    "FXM": 100000,
    "FXX": 200000,
    "FYI": 300000,
    "Food": 400000,
    "Fox Business": 150000,
    "Fox News": 300000,
    "Fox Sports 1": 150000,
    "Fox Sports 2": 100000,
    "Freeform": 300000,
    "Golf Channel": 300000,
    "GAC": 50000,
    "HGTV": 400000,
    "HLN": 100000,
    "Hallmark": 400000,
    "Hallmark Drama": 200000,
    "HMM": 200000,
    "Heroes & Icons": 100000,
    "History": 350000,
    "ID": 250000,
    "IFC": 100000,
    "LMN": 300000,
    "Lifetime": 350000,
    "Logo TV": 100000,
    "MLB Network": 150000,
    "MS Now": 250000,
    "MTV": 200000,
    "MTV2": 100000,
    "Magnolia Network": 150000,
    "MeTV": 300000,
    "MotorTrend": 150000,
    "NBC": 700000,
    "NFL Network": 300000,
    "NGW": 100000,
    "Nat Geo": 150000,
    "Nick Jr.": 150000,
    "Nick at Nite": 300000,
    "Nickelodeon": 300000,
    "OWN": 200000,
    "Outdoor Channel": 50000,
    "Oxygen": 150000,
    "Paramount": 200000,
    "Pop": 200000,
    "Reelz": 200000,
    "Science": 100000,
    "Smithsonian Channel": 100000,
    "Sundance": 100000,
    "SyFy": 200000,
    "TBS": 400000,
    "TLC": 250000,
    "TNT": 400000,
    "TV Land": 200000,
    "TV One": 150000,
    "Teen Nick": 150000,
    "Telemundo": 300000,
    "Travel": 200000,
    "TruTV": 400000,
    "UNIVERSO": 100000,
    "USA": 300000,
    "VH1": 200000,
    "WE": 170000,
}

# Helper function to convert time to hours. Used to determine max # of available dayparts 
def time_to_hours(time_str):
    if 'a' in time_str:
        raw_time = time_str.replace('a', '')
        suffix = 'AM'
    elif 'p' in time_str:
        raw_time = time_str.replace('p', '')
        suffix = 'PM'
    else:
        print(f'odd case of no a/p: {time_str} -- Q/A immediately')
        
    
    # Ensure the time string has a colon for strptime to parse correctly
    time_digits = ''.join([x for x in time_str if x.isdigit()])
    if len(time_digits) == 1:
        time_str = '0' + raw_time + ':00' + suffix
    elif len(time_digits) == 2:
        time_str = raw_time + ':00'+ suffix
    elif len(time_digits) == 3:
        time_str = raw_time[:-2] + ':' + raw_time[-2:] + suffix
    elif len(time_digits) == 4:
        time_str = time_str[:-2] + ':' + time_str[-2:] + suffix
        
    dt = datetime.strptime(time_str, '%I:%M%p') # expects 01:00AM
    return dt.hour + dt.minute / 60

# Function to parse a day range, given a campaigns start date
def parse_days(day_range, start_date, end_date, overlap):
    flight_start_date = datetime.strptime(start_date, '%Y-%m-%d').weekday() + 1
    flight_end_date = datetime.strptime(end_date, '%Y-%m-%d').weekday() + 1
    
    diff = 0
    if '-' in day_range:
        daypart_start_day, daypart_end_day = day_range.split('-')
        daypart_start_index = day_map[daypart_start_day]
        daypart_end_index = day_map[daypart_end_day]
        # If a daypart that spans multiple days starts before our campaigns flight start/end date, account for that difference here
        if flight_start_date > daypart_start_index: 
                diff += (flight_start_date - daypart_start_index)
        
        if flight_end_date < daypart_end_index: 
                diff += (daypart_end_index - flight_end_date)

        if daypart_end_index >= daypart_start_index:
            final =  (daypart_end_index - daypart_start_index + 1) - diff
        else:
            final =  (7 - daypart_start_index + daypart_end_index + 1) - diff
    else:
        return 1

    if overlap:
        return final
    else:
        return final + diff

# Function to parse a time range
def parse_time_range(time_range):
    start_time, end_time = time_range.split('-')
    start_hours = time_to_hours(start_time)
    end_hours = time_to_hours(end_time)
    return (end_hours - start_hours + 24) % 24

# See what quarter a date is in
def get_quarter(date_str):
    # Parse the date string into a datetime object
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Map to 2025-2026 quarter timeline
    year = date.year
    month = date.month
    
    if year == 2025:
        if month in [9, 10, 11, 12]:  # Sep,Oct-Dec 2025
            return '_4Q_25'
    elif year == 2026:
        if month in [1, 2, 3]:     # Jan-Mar 2026
            return '_1Q_26'
        elif month in [4, 5, 6]:   # Apr-Jun 2026
            return '_2Q_26'
        elif month in [7, 8, 9]:   # Jul-Sep 2026
            return '_3Q_26'
    
    # Default fallback
    return '_1Q_26'

def get_weeks(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    difference_in_days = (end_date - start_date).days + 1
    return difference_in_days // 7

# Check types of params, or if they're missing from the original form submission
def validate_form_params(form_data):
    if form_data['load_scheduler'] != '':
        pass
    else:
        del form_data['load_scheduler']
        if form_data['selectedDataset'] == 0:
            return {'error':'Please select a VideoAmp dataset.'}
        if form_data['start_date'] == '': 
            return {'error':'Please select a starting week.'}
        if form_data['end_date'] == '':
            return {'error':'Please select an ending week.'}
    if form_data['dark_weeks'] == '' or form_data['dark_weeks'] is None:
        form_data['dark_weeks'] = 0
    elif isinstance(form_data['dark_weeks'], str) and not form_data['dark_weeks'].isdigit():
        return {'error':'Please input a number for the dark weeks.'}
    elif not isinstance(form_data['dark_weeks'], (int, str)):
        return {'error':'Please input a number for the dark weeks.'}

    return form_data

# Adjust the math to include any adjustments to Nielsen Impressions & boost the VA impressions by the same %age
def map_custom_dayparts(unmapped_df: pd.DataFrame, df: pd.DataFrame, quarter:str):
    
    daypart_keys = { f"{row['Network']}|{row['Daypart']}|{row['Daypart Type']}".lower(): row.to_dict() for _, row in unmapped_df.transpose().iterrows() }
    for key, row in daypart_keys.items():
        # Ensure that we are not repeatedly boosting dayparts
        
        parts = key.split('|')  # Split from the right side into 3 parts
        network = parts[0]
        daypart = parts[1]
        daypart_type = parts[2]

        pertinent_row_index = df[(df['Network'].str.lower() == network) & 
                                (df['daypart_1'].str.lower() == daypart) & 
                                (df['Daypart_2'].str.lower() == daypart_type)].index
        
        # Update the 'nielsen_imps', 'va_imps', and 'midas_rate' columns only.
        
        if not pertinent_row_index.empty:
            pertinent_row_index = int(pertinent_row_index[0])
            
            # Fix column name mapping and handle comma-formatted numbers
            raw_nielsen = row.get('Age-Gender Imps', row.get('Nielsen Imps', '0'))
            raw_rates = row.get('CPM', '0')
            
            # Remove commas and convert to proper types
            new_nielsen = float(str(raw_nielsen).replace(',', ''))
            new_rates = float(str(raw_rates).replace(',', '').replace('$', ''))
            
            old_nielsen = float(df.iloc[pertinent_row_index]['_25_to_54_7days'])
            old_rates = float(df.iloc[pertinent_row_index][quarter])
            
            if old_nielsen != new_nielsen or old_rates != new_rates:
                nielsen_change_pct = new_nielsen / old_nielsen if old_nielsen > 0 else 1
                df.at[pertinent_row_index, '_25_to_54_7days'] = new_nielsen
                df.at[pertinent_row_index, 'impressions_per_unit'] *= nielsen_change_pct
                df.at[pertinent_row_index, f'decrypted_q{quarter}_A25_to_54'] = '$' + str(new_rates)
                print(f"Change %: {nielsen_change_pct}")
    return df

# Main function for the ranker
def ranker_main(form_data, client, session):
    to_add, to_remove, add_keys, remove_keys, ecpm_ceil = [], [], {}, {}, 10
    bundle = validate_form_params(form_data)
    if 'error' in bundle.keys():
        return bundle
    # Loading from previous session
    if 'load_scheduler' in form_data.keys():

        r = load_dataset_from_gcp(client, schedule_name=form_data['load_scheduler'])
        
        # Scheduler name not found
        if isinstance(r, dict) and "error" in r.keys():
            return r
        _, to_add, to_remove, budget, start_date, end_date, dark_weeks, selected_dataset = r
        

        # append new add/remove keys from submit, plus saved session keys, plus any others that have been added (or removed) in this session 
        if 'toAdd' in bundle.keys() and bundle['toAdd'] != '':
            to_add_list = list(to_add)
            to_add = bundle['toAdd'] + to_add_list + list(session['add_keys'].values())

            # if there's a duplicate, update (remove dups) with whatever comes first as that indicates the user is actively updating that key  
            to_add_copy = []
            seen_keys = set()
            for entry in to_add:
                daypart_key_filter = f"{entry['Network']} {entry['Daypart']} {entry['Network']} {entry['Daypart Type']}"
                if daypart_key_filter not in seen_keys:
                    seen_keys.add(daypart_key_filter)
                    to_add_copy.append(entry) 
            to_add = to_add_copy
            del to_add_copy

        if 'toRemove' in bundle.keys() and bundle['toRemove'] != '':
            to_remove_list = list(to_remove)
            to_remove = bundle['toRemove'] + to_remove_list + list(session['remove_keys'].values())
        session.modified = True
        

    # Indicates first time submitting 
    elif 'table1' not in form_data.keys():
        # Extract specific values by key to avoid unpacking issues with new spot percentage fields
        budget = bundle['budget']
        start_date = bundle['start_date'] 
        end_date = bundle['end_date']
        dark_weeks = bundle['dark_weeks']
        selected_dataset = bundle['selectedDataset']
        session['add_keys'] = {}
        session['remove_keys'] = {}
        session.modified = True
        

    # Indicates a resubmit and not loading from saved session
    else:
        # Extract specific values by key to avoid unpacking issues with new spot percentage fields
        to_add = bundle['toAdd']
        to_remove = bundle['toRemove'] 
        budget = bundle['budget']
        start_date = bundle['start_date']
        end_date = bundle['end_date']
        dark_weeks = bundle['dark_weeks']
        selected_dataset = bundle['selectedDataset']



    # Start calculations...
    quarter = get_quarter(start_date)
    weeks = get_weeks(start_date, end_date)

    # Join session keys & UI modifications to a single dict (for addition)
    all_adds = {
        **session['add_keys'],
        **{
            f"{d['Network']} {d['Daypart']} {d['Daypart Type']}": d
            for d in to_add
        }
    }
    # Join session keys & UI modifications to a single dict (for removal)
    all_removes = {
        **session['remove_keys'],
        **{
            f"{d['Network']} {d['Daypart']} {d['Daypart Type']}": d
            for d in to_remove
        }
    }
    dark_weeks = int(dark_weeks) if int(dark_weeks) >= 1 else 0
    weeks -= dark_weeks
    if weeks <= 8:
        return {'error': 'Please select flight dates that span at least eight weeks (this includes dark weeks).'}
    if dark_weeks >= weeks:
        return {'error': 'Please ensure the number of dark weeks is less than the number of flight weeks.'}
    budget = float(budget)


    # Extract networks to exclude (for backup network generation)

    exclude_networks = form_data.get('exclude_networks', [])
    is_backup_run = len(exclude_networks) > 0  # This indicates a backup network run
    print(f"DEBUG: Exclude networks = {exclude_networks}")

    # Extract Hispanic toggle from form data (defaults to False)
    include_hispanic = form_data.get('include_hispanic', False)

    # Grabs rates & VA/Nielsen data from BigQuery with Hispanic filtering
    print('[-] pulling data from BQ')
    df = get_combined_data(client, quarter, selected_dataset, include_hispanic)

    # TEMPORARY DEBUG - Check Broadcast column
    if 'Broadcast' in df.columns:
        print(f"[DEBUG] ✓ Broadcast column exists")
        abc_rows = df[df['network_og'] == 'abc']
        if len(abc_rows) > 0:
            sample_broadcast = abc_rows.iloc[0]['Broadcast']
            print(f"[DEBUG] ABC Broadcast value: {sample_broadcast} (type: {type(sample_broadcast).__name__})")
            print(f"[DEBUG] Testing == True: {sample_broadcast == True}")
            print(f"[DEBUG] Testing == 'true': {sample_broadcast == 'true'}")
            print(f"[DEBUG] Testing == 1: {sample_broadcast == 1}")
        broadcast_networks = df[df['Broadcast'] == True]['network_og'].unique()
        print(f"[DEBUG] Networks with Broadcast==True: {list(broadcast_networks)}")
    else:
        print(f"[DEBUG] ✗ Broadcast column NOT FOUND")
        print(f"[DEBUG] Available columns: {df.columns.tolist()}")
        
    if type(df) == dict and 'error' in df.keys():
        return {"error": f"Error grabbing data from GCP. (DEV) This may be because you are not using Q3 rates, or Choreograph stole my permissions again. GCP Error -- {df}"}

    # Validate dayparts are not added & removed
    for removal in remove_keys.keys():
        if removal in add_keys.keys():
            return {"error": "You chose a daypart to both add and remove. Please choose whether to add or remove a given daypart."}
    
    # Boost VA imps in case Nielsen is edited
    if len(all_adds) > 0:
        df = map_custom_dayparts(pd.DataFrame(all_adds), df, quarter) 

    # Passed validations for data pull/user input, start math
    print('[-] data pulled, doing math')
    all_primes_df = df[df['Prime'] == True]
    all_primes = list(df[df['Prime'] == True].drop_duplicates(subset=['network_og'])['network_og'])
    
    # Iterate over all of the Prime dayparts and map to network level so we can calculate 33% constraint in the ranker
    prime_daypart_vals = {}
    for _, row in all_primes_df.iterrows():

        if exclude_networks and row['network_og'] in exclude_networks:
            print(f"EXCLUDING NETWORK: {row['network_og']}")
            continue

        # Stakeholder requirement: to provide a comfortable buffer for inaccuracies in VideoAmp, we assert that the maximum ratio of VA imps:Nielsen Imps is 3:4
        #if row['impressions_per_unit'] > row['_25_to_54_7days']*.75:
            #row['impressions_per_unit'] = row['_25_to_54_7days']*.75

         # Apply network-specific VA discount if configured
        if row['network_og'] in network_va_discounts:
            discount_pct = network_va_discounts[row['network_og']]
            row['impressions_per_unit'] = row['impressions_per_unit'] * (1 - discount_pct / 100)
            print(f"[VA DISCOUNT] {row['network_og']}: {discount_pct}% discount applied to prime daypart")    

        # # If a network has multiple PDPs, choose the one with the lowest CPM. Logic may change when we GTM.
        if len(all_primes_df[all_primes_df['network_og'] == row['network_og']]) > 1:
            lowest_pdp_ecpm = all_primes_df[all_primes_df['network_og'] == row['network_og']]['cpm'].min()
            row = all_primes_df[(all_primes_df['network_og'] == row['network_og']) & (all_primes_df['cpm'] == lowest_pdp_ecpm)].iloc[0]


        midas_cost = (float(row['_25_to_54_7days'])  * float(row[quarter]) / 1000) * 2
        prime_impressions = row['impressions_per_unit']
        prime_daypart_vals[row['network_og']] = (midas_cost, prime_impressions, row['daypart']) 


    daypart_container = []
    
    # Calculate max spots + metrics for all dayparts
    for _, row in df.iterrows():
        
        # Stakeholder requirement: to provide a comfortable buffer for inaccuracies in VideoAmp, we assert that the maximum ratio of VA imps:Nielsen Imps is 3:4
        #if row['impressions_per_unit'] > row['_25_to_54_7days']*.75:
            #row['impressions_per_unit'] = row['_25_to_54_7days']*.75

        # Apply network-specific VA discount if configured
        if row['network_og'] in network_va_discounts:
            discount_pct = network_va_discounts[row['network_og']]
            row['impressions_per_unit'] = row['impressions_per_unit'] * (1 - discount_pct / 100)    

        requires_prime = True if row['network_og'] in all_primes else False
        midas_cost = (float(row['_25_to_54_7days'])  * float(row[quarter]) / 1000) 
        
        # Grab max number of dayparts (hours * days available) from join key
        daypart = row['Daypart_Lookup']
        day_time_blocks = daypart.split(' + ')
        daypart_hours = 0

        # In case of mirrored DPs/DPs with multiple slots, iterate over blocks
        for block in day_time_blocks:
            match = re.match(r'([MTWThFSaSu\-]+)\s+(\d+[apm]+-\d+[apm]+)', block)
            if match:
                days, times = match.groups()
                num_hours = parse_time_range(times)
                # Remember days only dont overlap for the first/last week (overlap for both weeks accounted for in parse_days), then campaign runs for full 7 days for weeks-1 weeks.
                daypart_hours += ((parse_days(days, start_date, end_date, overlap=False) * num_hours) * (weeks))
            else:
                print(f"no match on {block}")
        
        # More math
        videoamp_cpm = midas_cost * 1000 / row['impressions_per_unit']
        relevant_prime_daypart_name = ''
        va_imps = 0
        num_buys_relative_to_prime_daypart = 1
        prime_cost = 0
        try:
            if requires_prime and row['network_og'] in prime_daypart_vals:
                relevant_prime_daypart_name = prime_daypart_vals[row['network_og']][2]
                num_buys_relative_to_prime_daypart = round(prime_daypart_vals[row['network_og']][0] / midas_cost)
                if num_buys_relative_to_prime_daypart == 0:
                    num_buys_relative_to_prime_daypart = 1
                va_imps = row['impressions_per_unit'] * num_buys_relative_to_prime_daypart
                prime_cost = prime_daypart_vals[row['network_og']][0]/2
                midas_cost_final = midas_cost * num_buys_relative_to_prime_daypart
                total_cost = midas_cost_final + prime_cost 
                total_va_imps = va_imps + prime_daypart_vals[row['network_og']][1]
            
                ecpm = float(round(((total_cost/total_va_imps) * 1000), ndigits=2))
                args_qa = {
                    'network': row['network_og'],
                    'daypart_type': row['Daypart_2'],
                    'daypart_key': f"{row['network_og']} {row['daypart']} {row['Daypart_2']}",
                    'midas_rate': row[quarter],
                    'nielsen_imps': row['_25_to_54_7days'], # We are always using this for imps. May change in future.
                    'daypart': row['daypart'],
                    'max_daypart_buys': int(daypart_hours * 0.75), # account for buys on a weekly basis
                    'videoamp_imps': row['impressions_per_unit'],
                    'videoamp_cpm': videoamp_cpm,
                    'requires_prime': requires_prime,
                    'prime_value': prime_daypart_vals[row['network_og']][0],
                    'relevant_prime_daypart_name':relevant_prime_daypart_name,
                    'num_buys_relative_to_prime_daypart': num_buys_relative_to_prime_daypart,
                    "midas_cost_row": midas_cost,
                    "prime_cost": prime_cost,
                    "midas_cost_final": midas_cost_final,
                    "total_cost": float(total_cost), 
                    "total_va_imps":float(total_va_imps),
                    'ecpm': float(ecpm),
                    'Broadcast': row.get('Broadcast', False),
                    'Cable_News': row.get('Cable_News', False)
                }
            else:
                    args_qa = {
                    'network': row['network_og'],
                    'daypart_type': row['Daypart_2'],
                    'daypart_key': f"{row['network_og']} {row['daypart']} {row['Daypart_2']}",
                    'midas_rate': row[quarter],
                    'nielsen_imps': row['_25_to_54_7days'],
                    'daypart': row['daypart'],
                    'max_daypart_buys': int(daypart_hours * 0.75), # account for buys on a weekly basis
                    'videoamp_imps': row['impressions_per_unit'],
                    'videoamp_cpm': videoamp_cpm,
                    'requires_prime': requires_prime,
                    'prime_value': 0,
                    'relevant_prime_daypart_name':'',
                    'num_buys_relative_to_prime_daypart': '',
                    "midas_cost_row": midas_cost,
                    "prime_cost": 0,
                    "midas_cost_final": 0,
                    "total_cost": 0, 
                    "total_va_imps":0,
                    'ecpm': round(videoamp_cpm, ndigits=2),
                    'Broadcast': row.get('Broadcast', False),
                    'Cable_News': row.get('Cable_News', False)
                }
                                                                
        except Exception as e:
            print(f"Exception calculating CPM -- {e}")
            continue
        daypart_container.append(args_qa)
        
    # Extract dayparts to DF
    df = pd.DataFrame(daypart_container)
    results = {}
    max_ecpm = df['ecpm'].max()
    print('[-] math done, running LP')

    # Loop over results using smallest eCPM dayparts. We gradually expand 
    # the population size by 5 with each iteration until a feasable solution is found.
    # Track successful eCPM ceiling for backup generation
    final_ecpm_ceil = None

    # Extract network minimum override from form data
    network_minimum_override = form_data.get('network_minimum_override', None)

    require_broadcast = form_data.get('require_broadcast', False)

    require_cable_news = form_data.get('require_cable_news', False)
    # Extract spot length percentages from form data
    spots_15s_pct = float(form_data.get('spots_15s', 30)) / 100
    spots_30s_pct = float(form_data.get('spots_30s', 70)) / 100  
    spots_60s_pct = float(form_data.get('spots_60s', 0)) / 100
    spots_75s_pct = float(form_data.get('spots_75s', 0)) / 100
    spots_90s_pct = float(form_data.get('spots_90s', 0)) / 100

    # Calculate weighted average cost multiplier
    # :15 costs 0.5x, :30 costs 1.0x, :60 costs 2.0x, :75 costs 2.5x, :90 costs 3.0x
    spot_length_cost_multiplier = (spots_15s_pct * 0.5) + (spots_30s_pct * 1.0) + (spots_60s_pct * 2.0) + (spots_75s_pct * 2.5) + (spots_90s_pct * 3.0)

    print(f"[SPOT LENGTH ADJUSTMENT] Mix: {spots_15s_pct*100:.0f}% :15s, {spots_30s_pct*100:.0f}% :30s, {spots_60s_pct*100:.0f}% :60s, {spots_75s_pct*100:.0f}% :75s, {spots_90s_pct*100:.0f}% :90s")
    print(f"[SPOT LENGTH ADJUSTMENT] Cost multiplier: {spot_length_cost_multiplier:.3f}x")
    

    
    while type(results) == dict:  
        results = get_daypart_buys(df, budget, ecpm_ceil, add_keys=all_adds, remove_keys=all_removes, is_backup=is_backup_run, network_minimum_override=network_minimum_override, require_broadcast=require_broadcast, require_cable_news=require_cable_news, spot_length_cost_multiplier=spot_length_cost_multiplier)
        print(f'failed with ecpm_ceil {ecpm_ceil}')
        if type(results) != dict:  # Capture successful ceiling
            final_ecpm_ceil = ecpm_ceil
        ecpm_ceil+=5
        if ecpm_ceil >= max_ecpm:
            return {"error": "Impossible to solve given constraints...Contact aditya.harish@wppmedia.com "}

    # Generate backup networks (40% additional options)
    backup_networks = []
    if final_ecpm_ceil is not None:
        backup_min = final_ecpm_ceil
        backup_max = final_ecpm_ceil * 1.4  # 40% higher eCPM range
        
        # Get networks in backup eCPM range
        backup_df_temp = df[(df['ecpm'] >= backup_min) & (df['ecpm'] <= backup_max)].copy()
        
        if not backup_df_temp.empty:
            # Calculate target count (40% of primary results)
            primary_count = len([r for r in results if r.num_buys is not None and r.num_buys > 0])
            target_backup_count = max(int(primary_count * 0.4), 5)  # At least 5 backup options
            
            # Sort by eCPM and take top options
            backup_sorted = backup_df_temp.sort_values('ecpm').head(target_backup_count)
            
            # Convert to Daypart objects with calculated individual metrics
            for _, row in backup_sorted.iterrows():
                backup_networks.append(Daypart(
                    network=row['network'],
                    daypart_type=row['daypart_type'],
                    daypart=row['daypart'],
                    midas_cpm=float(row['midas_rate']),
                    videoamp_imps=row['videoamp_imps'],
                    nielsen_imps=row['nielsen_imps'],
                    videoamp_cpm=row['videoamp_cpm'],
                    requires_prime=row['requires_prime'],
                    relevant_prime_daypart_name=row['relevant_prime_daypart_name'],
                    num_buys_relative_to_prime_daypart=row['num_buys_relative_to_prime_daypart'],
                    ecpm=row['ecpm'],
                    midas_cost_row=row['midas_cost_row'],
                    num_buys=None,  # No optimization, just show as available option
                    broadcast=row.get('Broadcast', False),
                    cable_news=row.get('Cable_News', False)
                ))
            
            print(f'[+] Generated {len(backup_networks)} backup network options')

    # Convert both primary and backup results to dataframes
    df = Daypart.to_dataframe(results)
    backup_df = Daypart.to_dataframe(backup_networks)

    # Add "add_keys" to session memory.
    if len(to_add) > 0 or len(session['add_keys']) > 0:
        add_keys = {f"{row['Network']} {row['Daypart']} {row['Daypart Type']}": row for row in to_add}
        for key in add_keys:
            if key not in session.keys():
                session['add_keys'][key] = add_keys[key]
        session.modified = True

    # Add "remove_keys" to session memory.
    if len(to_remove) > 0 or len(session['remove_keys']) > 0:
        remove_keys = {f"{row['Network']} {row['Daypart']} {row['Daypart Type']}": row for row in to_remove}
        for key in remove_keys:
            session['remove_keys'][key] = remove_keys[key]
        session.modified = True

    print('[+] success')
    return {
        'success': df.sort_values(by=['network'], ascending=True),
        'backup': backup_df.sort_values(by=['network'], ascending=True) if not backup_df.empty else pd.DataFrame()
    }

# This is the algorithm for the scheduler.
def get_daypart_buys(df, budget, ecpm_ceil, add_keys, remove_keys, is_backup=False, network_minimum_override=None, require_broadcast=False, require_cable_news=False, spot_length_cost_multiplier=1.0):

    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    # Define the problem
    prob = pulp.LpProblem("Daypart_Optimization", pulp.LpMaximize)

    x = {}
    all_networks = []
    networks_in_use=[]
    used_daypart_keys = {}
    used_prime_daypart_keys = {}
    all_networks = []
    seen = []
    bonus = {}
    
    # Bonus features: there is an implicit bias in our minimization function towards minimizing the number of spots in order to produce a lower aggregate eCPM (var1(ecpm) + var2(ecpm)... + varn(ecpm)).
    # These bonuses address this by rewarding dayparts with low eCPMs and low costs.
    no_primes_df = df[~df['daypart_type'].str.lower().str.contains('prime')]
    top_10, top_20 = math.ceil(0.10 * len(no_primes_df)), math.ceil(0.20 * len(no_primes_df))
    df_sorted_by_cost = no_primes_df.sort_values(by='total_cost', ascending=True)
    bottom_10_percent_cost = df_sorted_by_cost.head(top_10)
    bottom_20_percent_cost = df_sorted_by_cost.head(top_20)
    top_20_percent_cost = df_sorted_by_cost.tail(top_20)
    df_sorted_by_ecpm = no_primes_df.sort_values(by='ecpm', ascending=True)
    top_20_percent_ecpm = df_sorted_by_ecpm.head(top_20)
    top_10_percent_ecpm = df_sorted_by_ecpm.head(top_10)
    top_10_percent_ecpm_keys = top_10_percent_ecpm['daypart_key'].tolist()
    top_20_percent_ecpm_keys = top_20_percent_ecpm['daypart_key'].tolist()

    
    top_ten_ecpm, top_twenty_ecpm, top_thirty_ecpm, top_half_ecpm = no_primes_df.ecpm.quantile(0.10), no_primes_df.ecpm.quantile(0.20), no_primes_df.ecpm.quantile(0.30), no_primes_df.ecpm.quantile(0.5)
    median_cost, bottom_ten_cost, bottom_twenty_cost, top_twenty_cost = no_primes_df.total_cost.median(), bottom_10_percent_cost['total_cost'].mean(), bottom_20_percent_cost['total_cost'].mean(), top_20_percent_cost['total_cost'].mean()
    

    # Addresses the edge case where a user may ONLY want to add a prime daypart (e.g., The Oscars, NFL Primetime, etc).
    if add_keys != []:
        prime_exclusive_adds = [x.split(' ')[0] for x in add_keys]
        for index in range(0, len(prime_exclusive_adds)):
            seen = []
            if prime_exclusive_adds[index] not in seen:
                seen.append(index)
        prime_exclusive_dayparts = [list(add_keys)[idx] for idx in seen if 'prime' in list(add_keys)[idx].lower()]
    
    # Get non-duplicates and their indices. All of these indices should be added to prime_exclusive if 'prime' is in the index's value.
    for _, row in df.iterrows():
        daypart_key = row['daypart_key']
        max_buys = row['max_daypart_buys']
        network = row['network']
        ecpm = row['ecpm']
        all_prime_dps_for_network = len([key for key in df[df['network'] == network]['daypart_key'] if 'prime' in key])
        all_dps_for_network = len([key for key in df[df['network'] == network]['daypart_key']])

        # This conditional removes inefficient buys from the algorithm. For a buy to be excluded: 
        # ecpm MUST exceed ceiling, 
        # it must NOT be a prime daypart, 
        # it must NOT be in the added keys. 
        # These constraints can be ignored if the only offered dayparts for a network are all prime. They're inefficient buys, so users can add themselves if need be.

        # Relax eCPM ceiling for backup networks (add 50% buffer)
        effective_ecpm_ceil = ecpm_ceil * 1.5 if is_backup else ecpm_ceil

        # Check if this daypart belongs to a broadcast network
        # Handle numpy bool_ type
        broadcast_val = row.get('Broadcast', False)
        is_broadcast_daypart = bool(broadcast_val) if broadcast_val is not None else False

        # Check if this daypart belongs to a cable news network
        cable_news_val = row.get('Cable_News', False)
        is_cable_news_daypart = bool(cable_news_val) if cable_news_val is not None else False

        # TEMPORARY DEBUG - check if broadcast dayparts are being filtered
        if network in ['ABC', 'CBS', 'NBC'] or (network.lower() in ['abc', 'cbs', 'nbc']):
            broadcast_val = row.get('Broadcast', False)
            is_broadcast_test = bool(broadcast_val) if broadcast_val is not None else False
            print(f"[DEBUG FILTER] {network} {daypart_key}: eCPM={ecpm}, ceiling={effective_ecpm_ceil}, Broadcast={broadcast_val}, is_broadcast={is_broadcast_test}, require_broadcast={require_broadcast}, will_bypass={require_broadcast and is_broadcast_test}")
            
        if ((ecpm >=  effective_ecpm_ceil) and daypart_key not in add_keys and 'prime' not in daypart_key.lower() and not (require_broadcast and is_broadcast_daypart) and daypart_key not in remove_keys) or all_prime_dps_for_network == all_dps_for_network or (require_cable_news and is_cable_news_daypart):
            continue
        total_cost = row['midas_cost_row']
        x[daypart_key] = pulp.LpVariable(f"daypart_{daypart_key}", lowBound=0, upBound=max_buys, cat='Integer')
        all_networks.append(network)
        if network not in used_daypart_keys:
            used_daypart_keys[network] = []
            networks_in_use.append(network)
        # Append the daypart_key and its associated cost to the network's list
        used_daypart_keys[network].append((daypart_key, total_cost))

        if 'prime' in daypart_key.lower():
            if network not in used_prime_daypart_keys:
                used_prime_daypart_keys[network] = []
            used_prime_daypart_keys[network].append((daypart_key, total_cost))


    # Calculate bonuses for the objective function
    print(f"Top 10% ECPM: {top_ten_ecpm} | Top 20% ECPM: {top_twenty_ecpm} | Top 30% ECPM: {top_thirty_ecpm} | Median cost: {median_cost} | Bottom 10% cost: {bottom_twenty_cost} | Top 20% Cost: {top_twenty_cost}" )
    for _, row in df.iterrows():
        if row['daypart_key'] in top_10_percent_ecpm_keys:
            bonus[row['daypart_key']] = 10
        elif row['daypart_key'] in top_20_percent_ecpm_keys:
            bonus[row['daypart_key']] = 4
        else:
            bonus[row['daypart_key']] = 1


        if row['ecpm'] <= top_ten_ecpm:
            bonus[row['daypart_key']] *= 20
        elif row['ecpm'] <= top_twenty_ecpm:
            bonus[row['daypart_key']] *= 4
        elif row['ecpm'] <= top_thirty_ecpm:
            bonus[row['daypart_key']] *= 2
        else:
            bonus[row['daypart_key']] /= 5

        # Specific case for 'reelz'
        if 'reelz' in row['daypart_key'] and row['ecpm'] <= top_twenty_ecpm:
            bonus[row['daypart_key']] *= 20

        # Penalty for high cost and high ecpm dayparts
        if row['total_cost'] >= median_cost and row['ecpm'] >= top_thirty_ecpm:
            bonus[row['daypart_key']] /= 1000
            if row['total_cost'] >= top_twenty_cost:
                # Overweight these dayparts to compensate for the high cost bias (chooses as few spots as possible to satisfy objective function) 
                bonus[row['daypart_key']] /= 50000000


        # Bonus for low cost and low ecpm dayparts
        if row['total_cost'] <= bottom_twenty_cost and row['ecpm'] <= top_twenty_ecpm:
            bonus[row['daypart_key']] *= 100
            if row['total_cost'] <= bottom_ten_cost:
                bonus[row['daypart_key']] *= 1000


        # Additional penalty for high eCPM
        if row['ecpm'] >= top_half_ecpm:
            bonus[row['daypart_key']] /= 5


    # Lower bound budget constraint (>=budget)
    # Adjust budget by spot length mix: if longer/more expensive spots, allocate fewer spots
    adjusted_budget = budget / spot_length_cost_multiplier
    prob += pulp.lpSum([x[row['daypart_key']] * row['midas_cost_row'] for _, row in df.iterrows() if row['daypart_key'] in x]) >= adjusted_budget

    # Upper bound budget constraint (<=105% of budget)
    prob += pulp.lpSum([x[row['daypart_key']] * row['midas_cost_row'] for _, row in df.iterrows() if row['daypart_key'] in x]) <= adjusted_budget * 1.05

    print(f"[BUDGET CONSTRAINT] Original budget: ${budget:,.2f}, Adjusted for spot lengths: ${adjusted_budget:,.2f} (/{spot_length_cost_multiplier:.3f})")


    # Exclude any daypart in remove_keys
    for daypart_key in remove_keys.keys():
        prob += x[daypart_key] <= 0

   # Prime daypart inclusion
    for _, row in df.iterrows():
        daypart_key = row['daypart_key']
       
        # Forcing dayparts to be in the solution set if selected in UI. Defaults to max # of dayparts if user sets
        if daypart_key in add_keys:
            # Leave the number of buys up to the algorithm if unspecified (nonzero)
            if add_keys[daypart_key]['Number of spots'] == 'nan' or add_keys[daypart_key]['Number of spots'].lower() == 'auto':
                prob += x[daypart_key] >= 10
            elif add_keys[daypart_key]['Number of spots'] == 'max':
                prob += x[daypart_key] >= x[daypart_key].upBound-10
                prob += x[daypart_key] <= x[daypart_key].upBound
            else:
                prob += x[daypart_key] >= float(add_keys[daypart_key]['Number of spots'])
                prob += x[daypart_key] <= float(add_keys[daypart_key]['Number of spots'])+1

        
        # Ensure the inclusion of the prime daypart in the solution set if the original daypart is included (unless the user is only trying to add a PDP)
        # Try/Except ensures that the prime_daypart_key is already in the potential solution set, accounting for if the PDP was selected 
        # for removal by the user (in remove_keys)
            try:
                prime_daypart_key = df[(df['daypart'] == row['relevant_prime_daypart_name']) & (df['network'] == row['network'])]['daypart_key'].iloc[0]
            except:
                prime_daypart_key = 'NOT FOUND'
            if (daypart_key in x and prime_daypart_key in x) and row['relevant_prime_daypart_name'] in df['daypart'].values and row['daypart_key'] not in remove_keys.keys():
                prob += x[prime_daypart_key] >= x[daypart_key]

    # Set prime DP cost constraint

        # Set prime DP cost constraint
    for network in used_prime_daypart_keys.keys():

        # If the only daypart added in a given network is prime, we ignore the 33% rule.
        if network in [x.split(' ')[0] for x in prime_exclusive_dayparts]:
            continue

        # Calculate the total cost of all dayparts for this network
        total_cost = pulp.lpSum([cost * x[daypart_key] for daypart_key, cost in used_daypart_keys[network]])

        # Calculate the total cost of prime dayparts for this network
        prime_cost = pulp.lpSum([cost * x[daypart_key] for daypart_key, cost in used_prime_daypart_keys[network]])
        
        # Constraint: Prime dayparts cost must be at least 33% of the total cost for this network
        prob += prime_cost >= 0.33 * total_cost
        prob += prime_cost <= 0.5 * total_cost
        
    # Constraint: Adhere to the guaranteed minimums for the networks
    constrained = []
    for network, daypart_keys in used_daypart_keys.items():
        # Create a binary variable to indicate if the network is used
        network_used = pulp.LpVariable(f"network_used_{network}", cat='Binary')

        # Link daypart spend to network usage
        for daypart_key, _ in daypart_keys:
            if daypart_key in x:
                # Ensure that if the network is not used, x[daypart_key] = 0
                # Use the actual upper bound of x[daypart_key]
                M = x[daypart_key].upBound if x[daypart_key].upBound is not None else 200
                prob += x[daypart_key] <= network_used * M


        # Sum up the spend across all dayparts for this network (needed for both paths)
        network_spend = pulp.lpSum([
            cost * x[daypart_key] 
            for daypart_key, cost in daypart_keys if daypart_key in x
        ])

        # If network is used, enforce the minimum spend
        if network_minimum_override is not None:
            # Custom minimum is enabled - apply uniform minimum to all networks
            network_min = network_minimum_override
            constrained.append(network)
            prob += network_spend >= network_min * network_used
        else:
            # Use default hardcoded minimums
            desired_network_min = [(n, v) for n, v in guaranteed_minimums.items() if network.lower() == n.lower()]
            if len(desired_network_min) == 1 and isinstance(desired_network_min[0][1], int):
                network_min = desired_network_min[0][1]
                constrained.append(network)
                prob += network_spend >= network_min * network_used
        # Constraint: Enforce network maximums
        desired_network_max = [(n, v) for n, v in guaranteed_maximums.items() if network.lower() == n.lower()]
        if len(desired_network_max) == 1 and isinstance(desired_network_max[0][1], int):
            network_max = desired_network_max[0][1]
            prob += network_spend <= network_max * network_used
            print(f"[CONSTRAINT] {network} maximum: ${network_max:,}")

        # Constraint: Require at least one broadcast network if flag is set
    if require_broadcast:
        # Get broadcast networks from the dataframe
        # Handle numpy bool_ type - convert to boolean
        if 'Broadcast' in df.columns:
            broadcast_networks = df[df['Broadcast'].astype(bool) == True]['network'].unique().tolist()
        else:
            broadcast_networks = []
        
        if broadcast_networks:
            # Collect broadcast network binary variables
            broadcast_used_vars = []
            for bcast_network in broadcast_networks:
                # Check if this network has any dayparts in the solution
                if bcast_network in used_daypart_keys:
                    # Find the network_used variable we created earlier
                    for var in prob.variables():
                        if var.name == f"network_used_{bcast_network}":
                            broadcast_used_vars.append(var)
                            break
            
            if broadcast_used_vars:
                # At least ONE broadcast network must be used (sum of binary vars >= 1)
                prob += pulp.lpSum(broadcast_used_vars) == 1
                print(f"[CONSTRAINT] Requiring at least one broadcast network from: {broadcast_networks}")
            else:
                print(f"[WARNING] Broadcast required but no broadcast networks found in optimization variables")
        else:
            print(f"[WARNING] Broadcast required but no broadcast networks found in data")

    
    # Constraint: Exclude all cable news network if flag is set
    if require_cable_news:
        # Get cable news networks from the dataframe
        # Handle numpy bool_ type - convert to boolean
        if 'Cable_News' in df.columns:
            cable_news_networks = df[df['Cable_News'].astype(bool) == True]['network'].unique().tolist()
        else:
            cable_news_networks = []
        
        if cable_news_networks:
            # Collect cable news network binary variables
            cable_news_used_vars = []
            for cn_network in cable_news_networks:
                # Check if this network has any dayparts in the solution
                if cn_network in used_daypart_keys:
                    # Find the network_used variable we created earlier
                    for var in prob.variables():
                        if var.name == f"network_used_{cn_network}":
                            cable_news_used_vars.append(var)
                            break
            
            if cable_news_used_vars:
                # NO cable news networks should be used be used (sum of binary vars == 1)
                prob += pulp.lpSum(cable_news_used_vars) == 0
                print(f"[CONSTRAINT] Excluding all cable news network from: {cable_news_networks}")
            else:
                print(f"[WARNING] Cable news exclusion requested but no cable news networks found in optimization variables")
        else:
            print(f"[WARNING] Cable news exclusion requested but no cable news networks found in data")        

    # Objective function: maximize bonus scores. These values have been QA'd extensively. Do not change.
    bonus_weight = 31.667
    cost_penalty_weight = 1.1

    # Calculate total bonus scores within the LP problem
    total_bonus = pulp.lpSum([
        bonus[row['daypart_key']] * x[row['daypart_key']] 
        for _, row in df.iterrows() 
        if row['daypart_key'] in x
    ])

    # Calculate total cost within the LP problem
    total_cost = pulp.lpSum([
        row['total_cost'] * x[row['daypart_key']] 
        for _, row in df.iterrows() 
        if row['daypart_key'] in x
    ])

    # Define the objective function: maximize total bonus minus a penalty for total cost
    objective = bonus_weight * total_bonus - cost_penalty_weight * total_cost

    # Set the objective in the problem
    prob.setObjective(objective)
    

    # Solve the problem
    prob.solve()
    if prob.status == pulp.LpStatusInfeasible:
        return {"error": "Impossible to solve this solution. (DEV) Consider eliminating upper bounds of Prime DP or budget constraint here..."}
    result = to_daypart_results(df, x)
    return result

def to_daypart_results(df, x):
    all_dayparts = []
    for _, row in df.iterrows():
        daypart_key = row['daypart_key']
        if daypart_key in x and x[daypart_key].varValue is not None and x[daypart_key].varValue > 0:
            network = row['network']
            daypart_type = row['daypart_type']
            daypart_name = row['daypart']
            midas_cpm = float(row['midas_rate'])           
            videoamp_imps = row['videoamp_imps']
            nielsen_imps = row['nielsen_imps']
            videoamp_cpm = row['videoamp_cpm']
            requires_prime = row['requires_prime']
            midas_cost_row = row['midas_cost_row']
            relevant_prime_daypart_name = row['relevant_prime_daypart_name']
            num_buys_relative_to_prime_daypart = row['num_buys_relative_to_prime_daypart']
            ecpm = row['ecpm']

            daypart = Daypart(
                network=network,
                daypart_type=daypart_type,
                daypart=daypart_name,
                midas_cpm=midas_cpm,
                videoamp_imps=videoamp_imps,
                nielsen_imps=nielsen_imps,
                videoamp_cpm=videoamp_cpm,
                requires_prime=requires_prime,
                relevant_prime_daypart_name=relevant_prime_daypart_name,
                num_buys_relative_to_prime_daypart=num_buys_relative_to_prime_daypart,
                ecpm=ecpm,
                midas_cost_row=midas_cost_row,
                num_buys=int(x[daypart_key].varValue),
                broadcast=row.get('Broadcast', False),
                cable_news=row.get('Cable_News', False)
            )

        else:
            network = row['network']
            daypart_type = row['daypart_type']
            daypart_name = row['daypart']
            midas_cpm = float(row['midas_rate'])
            videoamp_imps = row['videoamp_imps']
            nielsen_imps = row['nielsen_imps']
            videoamp_cpm = row['videoamp_cpm']
            requires_prime = row['requires_prime']
            midas_cost_row = row['midas_cost_row']
            relevant_prime_daypart_name = row['relevant_prime_daypart_name']
            num_buys_relative_to_prime_daypart = row['num_buys_relative_to_prime_daypart']
            ecpm = row['ecpm']

            daypart = Daypart(
                network=network,
                daypart_type=daypart_type,
                daypart=daypart_name,
                videoamp_imps=videoamp_imps,
                midas_cpm=midas_cpm,
                nielsen_imps=nielsen_imps,
                videoamp_cpm=videoamp_cpm,
                requires_prime=requires_prime,
                relevant_prime_daypart_name=relevant_prime_daypart_name,
                num_buys_relative_to_prime_daypart=num_buys_relative_to_prime_daypart,
                ecpm=ecpm,
                midas_cost_row=midas_cost_row,
                num_buys=None,
                broadcast=row.get('Broadcast', False),
                cable_news=row.get('Cable_News', False)
            )

        all_dayparts.append(daypart)

    return all_dayparts