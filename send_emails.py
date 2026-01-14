import os
import sys
import smtplib
from email.message import EmailMessage
from notion_client import Client

# This function ensures logs appear in GitHub Actions immediately
def log(msg):
    print(msg, flush=True)

def main():
    log("--- SCRIPT INITIALIZING ---")
    
    # Check Secrets
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not token:
        log("❌ ERROR: NOTION_TOKEN is empty. Check your AUTO_DISPATCHER secret mapping.")
        return
    if not db_id:
        log("❌ ERROR: NOTION_DATABASE_ID is empty.")
        return

    notion = Client(auth=token)

    # 1. Query Notion
    log(f"Searching for 'Ready to Send' in Database {db_id}...")
    try:
        results = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Status",
                "status": {"equals": "Ready to Send"}
            }
        ).get("results")
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    log(f"Found {len(results)} rows ready for processing.")

    if not results:
        log("Stopping: No rows found. Ensure Notion status is exactly 'Ready to Send'.")
        return

    # 2. Setup Email
    log("Connecting to SMTP...")
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
        log("✅ Gmail Login Successful.")
    except Exception as e:
        log(f"❌ EMAIL LOGIN ERROR: {e}")
        return

    # 3. Execution
    for page in results:
        try:
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            email_addr = page["properties"]["Email"]["email"]
            
            log(f"Sending to {contact_name}...")

            msg = EmailMessage()
            msg['Subject'] = "Tulum Project Update"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name}, this is a successful automation test.")
            
            smtp.send_message(msg)
            log(f"✅ Sent to {email_addr}")

            # Update status to 'Sent'
            notion.pages.update(
                page_id=page["id"],
                properties={"Status": {"status": {"name": "Sent"}}}
            )
            log(f"🔄 Notion updated for {contact_name}")

        except Exception as e:
            log(f"❌ ROW ERROR: {e}")

    smtp.quit()
    log("--- SCRIPT COMPLETE ---")

if __name__ == "__main__":
    main()
