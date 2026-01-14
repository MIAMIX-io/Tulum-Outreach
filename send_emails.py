import os
import smtplib
from email.message import EmailMessage

# IMPORTANT: explicit import to avoid CI SDK bug
from notion_client.client import Client


def log(msg):
    print(msg, flush=True)


def main():
    log("--- SCRIPT INITIALIZING ---")

    # Load secrets
    NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
    DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        log("❌ ERROR: One or more required environment variables are missing.")
        return

    # Init Notion client
    notion = Client(auth=NOTION_TOKEN)

    # Safety check — fail loudly if SDK is wrong
    if not hasattr(notion.databases, "query"):
        raise RuntimeError(
            f"Broken Notion SDK loaded: {type(notion.databases)}"
        )

    # 1. Query Notion
    log(f"Searching for 'Ready to Send' in Database {DATABASE_ID}...")
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
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

    # 2. SMTP setup
    log("Connecting to Gmail SMTP...")
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        log("✅ Gmail login successful.")
    except Exception as e:
        log(f"❌ EMAIL LOGIN ERROR: {e}")
        return

    # 3. Send emails
    for page in results:
        try:
            props = page["properties"]

            # Contact name (safe)
            title = props["Contact"]["title"]
            contact_name = title[0]["plain_text"] if title else "there"

            # Email (required)
            email_addr = props["Email"].get("email")
            if not email_addr:
                raise ValueError("Missing email address")

            log(f"Sending email to {contact_name} <{email_addr}>")

            msg = EmailMessage()
            msg["Subject"] = "Tulum Project Update"
            msg["From"] = EMAIL_USER
            msg["To"] = email_addr
            msg.set_content(
                f"Hi {contact_name},\n\n"
                "This is a successful automation test.\n\n"
                "Best regards,\n"
                "MIAMIX"
            )

            smtp.send_message(msg)
            log(f"✅ Email sent to {email_addr}")

            # 4. Update Notion status
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Status": {
                        "select": {"name": "Sent"}
                    }
                }
            )
            log(f"🔄 Notion updated → Sent ({contact_name})")

        except Exception as e:
            log(f"❌ ROW ERROR ({page.get('id')}): {e}")

    smtp.quit()
    log("--- SCRIPT COMPLETE ---")


if __name__ == "__main__":
    main()
