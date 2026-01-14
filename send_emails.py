import os
import sys
import smtplib
from email.message import EmailMessage
from notion_client import Client

# Force every print to show up in GitHub Logs immediately
def log(msg):
    print(msg, flush=True)

def main():
    log("--- SCRIPT STARTING ---")
    
    # Load Environment Variables
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASSWORD")

    if not token:
        log("❌ ERROR: NOTION_TOKEN (from AUTO_DISPATCHER secret) is empty!")
        return

    notion = Client(auth=token)

    # 1. Query Notion
    log(f"Querying Notion Database: {db_id}...")
    try:
        results = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Status",
                "status": {"equals": "Ready to Send"}
            }
        ).get("results")
    except Exception as e:
        log(f"❌ NOTION ERROR: {e}")
        return

    log(f"Found {len(results)} rows with 'Ready to Send' status.")

    if not results:
        log("Stopping: No contacts found. Verify your Notion status is exactly 'Ready to Send'.")
        return

    # 2. Setup Email
    log("Connecting to Gmail...")
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(email_user, email_pass)
        log("✅ Gmail Login Successful.")
    except Exception as e:
        log(f"❌ GMAIL ERROR: {e}")
        return

    # 3. Send and Update
    for page in results:
        try:
            name = page["properties"]["Contact"]["title"][0]["plain_text"]
            email = page["properties"]["Email"]["email"]
            log(f"Processing: {name} <{email}>")

            msg = EmailMessage()
            msg['Subject'] = "Tulum Project Follow-up"
            msg['From'] = email_user
            msg['To'] = email
            msg.set_content(f"Hi {name},\n\nAutomated message successful.")
            
            smtp.send_message(msg)
            log(f"✅ Email sent to {name}")

            notion.pages.update(
                page_id=page["id"],
                properties={"Status": {"status": {"name": "Sent"}}}
            )
            log(f"🔄 Notion status updated to 'Sent' for {name}")

        except Exception as e:
            log(f"❌ Error on row: {e}")

    smtp.quit()
    log("--- SCRIPT FINISHED ---")

if __name__ == "__main__":
    main()
