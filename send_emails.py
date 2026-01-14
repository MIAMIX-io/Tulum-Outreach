import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    print("--- DEBUGGING START ---")
    
    # 1. SUPER DEBUG: Let's see what is actually in the database
    all_rows = notion.databases.query(database_id=DATABASE_ID, page_size=5).get("results")
    print(f"Total rows checked for debug: {len(all_rows)}")
    for i, row in enumerate(all_rows):
        name = row["properties"]["Contact"]["title"][0]["plain_text"]
        status_data = row["properties"]["Status"]["status"]
        print(f"Row {i+1}: '{name}' has Status name: '{status_data['name']}'")
    
    print("--- FILTERED QUERY START ---")

    # 2. The Actual Filtered Query
    try:
        results = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Status",
                "status": {
                    "equals": "Ready to Send"
                }
            }
        ).get("results")
    except Exception as e:
        print(f"API Error: {e}")
        return

    print(f"Found {len(results)} rows matching 'Ready to Send'")

    if not results:
        print("Stopping: No matches found. Check the DEBUG list above for exact naming.")
        return

    # 3. Email Logic
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
        
        for page in results:
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            email_addr = page["properties"]["Email"]["email"]
            page_id = page["id"]

            print(f"Sending email to {contact_name}...")
            msg = EmailMessage()
            msg['Subject'] = "Tulum Project Test"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name}, test successful.")
            smtp.send_message(msg)

            # Update to Sent
            notion.pages.update(
                page_id=page_id,
                properties={"Status": {"status": {"name": "Sent"}}}
            )
            print(f"✅ Success: {contact_name} moved to Sent")
        
        smtp.quit()
    except Exception as e:
        print(f"Email/Update Error: {e}")

if __name__ == "__main__":
    main()
