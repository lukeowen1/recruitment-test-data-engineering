"""
A script to ingest data from CSV files into a MySQL database.
It reads people and places data, inserts them into the database, and handles foreign key relationships.
"""

#!/usr/bin/env python3
# images/data-ingest/ingest.py

import mysql.connector
import pandas as pd
import os
import time
import sys
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        # database config
        'db_host': os.getenv('DB_HOST', 'database'),
        'db_user': os.getenv('DB_USER', 'codetest'),
        'db_password': os.getenv('DB_PASSWORD', 'swordfish'),
        'db_name': os.getenv('DB_NAME', 'codetest'),
        'db_port': int(os.getenv('DB_PORT', '3306')),
        
        # file paths
        'data_path': os.getenv('DATA_PATH', '/app/data'),
        'people_file': os.getenv('PEOPLE_FILE', 'people.csv'),
        'places_file': os.getenv('PLACES_FILE', 'places.csv'),
        
        # processing config
        'max_retries': int(os.getenv('MAX_DB_RETRIES', '30')),
        'encoding': os.getenv('FILE_ENCODING', 'utf-8'),
    }

def wait_for_database(config: Dict[str, Any], max_retries: int = 30) -> None:
    """Wait for database to be ready."""
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(**config)
            conn.close()
            print("Database is ready!")
            return
        except mysql.connector.Error as e:
            print(f"Attempt {attempt + 1}: Database not ready. Waiting... ({e})")
            time.sleep(2)
    
    raise Exception("Database not available after maximum retries")

def load_places_data(cursor, data_path: str) -> Dict[str, int]:
    """Load places data and return mapping of place descriptions to IDs"""
    places_file = os.path.join(data_path, 'places.csv')
    
    if not os.path.exists(places_file):
        raise FileNotFoundError(f"Places file not found: {places_file}")
    
    # read places CSV
    places_df = pd.read_csv(places_file, encoding='utf-8')
    city_to_id_mapping = {}
    
    print(f"Loading {len(places_df)} places...")
    
    for _, row in places_df.iterrows():
        city = row['city'].strip()
        county = row['county'].strip() if pd.notna(row['county']) else None
        country = row['country'].strip()
        
        # insert to get place ID
        insert_query = """
        INSERT INTO places (city, county, country) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
        """
        
        cursor.execute(insert_query, (city, county, country))
        place_id = cursor.lastrowid
        
       # simple mapping: city name -> place ID
        city_to_id_mapping[city.lower()] = place_id
    
    print(f"Loaded {len(city_to_id_mapping)} unique places")
    return city_to_id_mapping

def load_people_data(cursor, data_path: str, city_to_id_mapping: Dict[str, int]) -> None:
    """Load people data using place ID mapping"""
    people_file = os.path.join(data_path, 'people.csv')
    
    if not os.path.exists(people_file):
        raise FileNotFoundError(f"People file not found: {people_file}")
    
    # read people CSV
    people_df = pd.read_csv(people_file, encoding='utf-8')
    
    print(f"Loading {len(people_df)} people...")
    
    successful_inserts = 0
    failed_inserts = 0
    
    for _, row in people_df.iterrows():
        try:
            first_name = row['given_name'].strip()
            last_name = row['family_name'].strip()
            date_of_birth = row['date_of_birth']
            city_of_birth = row['place_of_birth'].strip()
            
            # simple city matching - just look up the city name
            place_id = city_to_id_mapping.get(city_of_birth.lower())
            
            if place_id is None:
                print(f"Warning: Could not find place ID for {city_of_birth}")
                failed_inserts += 1
                continue
            
            # insert person
            insert_query = """
            INSERT INTO people (first_name, last_name, date_of_birth, place_of_birth_id)
            VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (first_name, last_name, date_of_birth, place_id))
            successful_inserts += 1
            
        except Exception as e:
            print(f"Error inserting person {row.get('first_name', 'Unknown')}: {e}")
            failed_inserts += 1
    
    print(f"Successfully inserted {successful_inserts} people, failed: {failed_inserts}")

def main():
    """Main ingest function"""
    print("Starting data ingest...")

    # get configuration from environment variables
    config = get_config()
    
    # database configuration
    db_config = {
        'host': config['db_host'],
        'user': config['db_user'],
        'password': config['db_password'],
        'database': config['db_name'],
        'charset': 'utf8mb4'
    }
    
    data_path = 'data/'
    
    try:
        # wait for database to be ready
        wait_for_database(db_config)
        
        # connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # clear existing data before loading new data
        print("Clearing existing data...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")  # disable foreign key checks
        cursor.execute("TRUNCATE TABLE people")        # clear people first (has foreign key)
        cursor.execute("TRUNCATE TABLE places")        # clear places
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")   # re-enable foreign key checks
        conn.commit()
        print("Existing data cleared.")
        cursor = conn.cursor()
        
        # load places first (for foreign key references)
        place_id_mapping = load_places_data(cursor, data_path)
        conn.commit()
        
        # load people data
        load_people_data(cursor, data_path, place_id_mapping)
        conn.commit()
        
        print("Data ingest completed successfully!")

        # show places table count to check 
        cursor.execute("SELECT COUNT(*) FROM places")
        place_count = cursor.fetchone()[0]
        print(f"\nPlaces table: {place_count} total records")
        
        # show people table count to check
        cursor.execute("SELECT COUNT(*) FROM people")
        people_count = cursor.fetchone()[0]
        print(f"\nPeople table: {people_count} total records")
        
    except Exception as e:
        print(f"Error during data ingest: {e}")
        sys.exit(1)
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()