"""
This script connects to a MySQL database, retrieves country counts from the `places` and `people` tables, and outputs the results to a JSON file.
It waits for the database to be ready before executing queries and handles exceptions during the process.
"""
#!/usr/bin/env python3
# images/data-output/output.py

import mysql.connector
import json
import os
import time
import sys
from typing import Dict, Any, List

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
        'data_path': os.getenv('DATA_PATH', '/data'),
        'output_file': os.getenv('OUTPUT_FILE', 'summary_output.json'),
        
        # processing config
        'encoding': os.getenv('FILE_ENCODING', 'utf-8'),
    }

def wait_for_database(config: Dict[str, Any], max_retries: int = 30) -> None:
    """Wait for database to be ready"""
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

def generate_summary_output(cursor) -> List[Dict[str, Any]]:
    """Generate summary output with country counts"""
    
    # query to get country counts
    query = """
    SELECT 
        pl.country,
        COUNT(p.id) as people_count
    FROM places pl
    LEFT JOIN people p ON pl.id = p.place_of_birth_id
    GROUP BY pl.country
    ORDER BY people_count DESC, pl.country ASC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    summary_data = {}
    for country, count in results:
        summary_data[country] = count
    
    return summary_data

def main():
    """Main output function."""
    print("Starting data output generation...")

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
    
    output_path = os.path.join(config['data_path'], config['output_file'])
    
    try:
        # wait for database to be ready
        wait_for_database(db_config)
        
        # connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # generate summary data
        summary_data = generate_summary_output(cursor)
        
        # write to JSON file
        with open(output_path, 'w', encoding=config['encoding']) as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"Summary output written to {output_path}")
        print(f"Generated summary for {len(summary_data)} countries")
        
        # print summary for verification
        print("\nSummary preview:")
        for country, count in summary_data.items():
            print(f"  {country}: {count} people")
        
    except Exception as e:
        print(f"Error during output generation: {e}")
        sys.exit(1)
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()