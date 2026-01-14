import os
from notion_client import Client

# Force immediate output to GitHub logs
def log(msg):
    print(msg, flush=True)

def main():
    log("--- STARTING DIAGNOSTIC RUN ---")
    
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")

    if not token:
        log("❌ ERROR: NOTION_TOKEN is missing.")
        return
    if not db_id:
        log("❌ ERROR: NOTION_DATABASE_ID is missing.")
        return

    notion = Client(auth=token)

    # 1. TEST CONNECTION & PULL RAW DATA
    log(f"Testing connection to Database: {db_id}")
    try:
        # Use the specific syntax for the latest notion-client
        response = notion.databases.query(database_id=db_id)
        results = response.get("results", [])
        log(f"✅ CONNECTION SUCCESS! Found {len(results)} total rows in the database.")
    except Exception as e:
        log(f"❌ CONNECTION FAILED: {e}")
        log("Check: Is the 'Auto Dispatcher' invited to this specific Notion page?")
        return

    # 2. ANALYZE FIRST 3 ROWS (The "Super Debug")
    log("--- ANALYZING FIRST 3 ROWS ---")
    for i, page in enumerate(results[:3]):
        try:
            # Extract Contact Name
            contact_name = "Unknown"
            title_prop = page["properties"].get("Contact", {}).get("title", [])
            if title_prop:
                contact_name = title_prop[0]["plain_text"]

            # Extract Status Info
            status_obj = page["properties"].get("Status", {})
            status_type = status_obj.get("type", "unknown")
            
            # This is the gold: what is the actual name of the status?
            actual_name = "N/A"
            if status_type == "status":
                actual_name = status_obj.get("status", {}).get("name")
            elif status_type == "select":
                actual_name = status_obj.get("select", {}).get("name")

            log(f"Row {i+1}: '{contact_name}' | Type: {status_type} | Current Value: '{actual_name}'")
        except Exception as e:
            log(f"Could not read row {i+1}: {e}")

    # 3. TRY THE SPECIFIC FILTER
    log("--- TESTING TRIGGER FILTER ---")
    log("Searching for: Status == 'Ready to Send'")
    
    # We will search manually through the results to avoid API filter syntax errors
    matches = 0
    for page in results:
        status_obj = page["properties"].get("Status", {})
        current_val = ""
        if status_obj.get("type") == "status":
            current_val = status_obj.get("status", {}).get("name")
        
        if current_val == "Ready to Send":
            matches += 1
            name = page["properties"]["Contact"]["title"][0]["plain_text"]
            log(f"🎯 MATCH FOUND: {name}")

    if matches == 0:
        log("❌ No rows matched 'Ready to Send'. Double check spelling/capitalization.")
    else:
        log(f"✅ Found {matches} rows ready for email code.")

if __name__ == "__main__":
    main()
