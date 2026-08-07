import requests

# Configuration
SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ"
TABLE_NAME = "test_events"

# Endpoint URL requesting all columns (*)
url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*"

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}

all_rows = []
chunk_size = 1000
start = 0

print("Fetching dataset from Supabase...")

while True:
    # Supabase uses zero-indexed, inclusive ranges for pagination
    range_header = f"{start}-{start + chunk_size - 1}"
    current_headers = {**headers, "Range": range_header}
    
    response = requests.get(url, headers=current_headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        break
        
    chunk = response.json()
    if not chunk:
        break
        
    all_rows.extend(chunk)
    print(f"Fetched rows {start} to {start + len(chunk) - 1}...")
    
    # If we received fewer rows than the chunk size, we've reached the end
    if len(chunk) < chunk_size:
        break
        
    start += chunk_size

print(f"\nSuccessfully fetched a total of {len(all_rows)} rows.")

# Example: Print the first row to inspect structure
if all_rows:
    print("\nSample Row:")
    print(all_rows[0])
