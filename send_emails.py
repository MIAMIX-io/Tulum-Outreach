import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

def log(msg):
    print(msg, flush=True)

def main():
    log("--- SCRIPT INITIALIZING ---")

    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")

    if not token or not db_id:
        log("❌ ERROR: Missing Notion credentials.")
        return

    notion = Client(auth=token)

    log(f"Searching for 'Ready to Send' in Database {db_id}...")
    try:
        response = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Status",
                "select": {"equals": "Ready to Send"}
            }
        )
        results = response.get("results", [])
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    log(f"Found {len(results)} rows ready for processing.")

    if not results:
        log("Stopping: No rows found.")
        return

    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
        log("✅ Gmail Login Successful.")
    except Exception as e:
        log(f"❌ EMAIL LOGIN ERROR: {e}")
        return

    for page in results:
        try:
            title = page["properties"]["Contact"]["title"]
            contact_name = title[0]["plain_text"] if title else "there"

            email_addr = page["properties"]["Email"].get("email")
            if not email_addr:
                raise ValueError("Missing email")

            log(f"Sending to {contact_name} <{email_addr}>")

            msg = EmailMessage()
            msg["Subject"] = "Tulum Project Update"
            msg["From"] = os.environ["EMAIL_USER"]
            msg["To"] = email_addr
            msg.set_content(f"Hi {contact_name}, this is a successful automation test.")

            smtp.send_message(msg)
            log(f"✅ Sent to {email_addr}")

            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Status": {"select": {"name": "Sent"}}
                }
            )
            log(f"🔄 Notion updated for {contact_name}")

        except Exception as e:
            log(f"❌ ROW ERROR: {e}")

    smtp.quit()
    log("--- SCRIPT COMPLETE ---")

if __name__ == "__main__":
    main()
