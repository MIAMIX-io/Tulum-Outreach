import os
import smtplib
from email.message import EmailMessage
from notion_client import Client


def log(msg):
    print(msg, flush=True)


def main():
    log("--- SCRIPT INITIALIZING ---")

    # Environment variables
    NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
    DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        log("❌ ERROR: Missing required environment variables.")
        return

    # Initialize Notion client
    notion = Client(auth=NOTION_TOKEN)

    # Query Notion with STATUS + SEND EMAIL gate
    log("Querying Notion for contacts ready to send...")
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "and": [
                    {
                        "property": "Status",
                        "status": {"equals": "Ready to Send"}
                    },
                    {
                        "property": "Send Email",
                        "select": {"equals": "Yes"}
                    }
                ]
            }
        )
        results = response.get("results", [])
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    log(f"Found {len(results)} contacts ready to email.")

    if not results:
        log("Stopping: No eligible rows found.")
        return

    # SMTP setup
    log("Connecting to Gmail SMTP...")
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        log("✅ Gmail login successful.")
    except Exception as e:
        log(f"❌ EMAIL LOGIN ERROR: {e}")
        return

    # Send emails
    for page in results:
        try:
            props = page["properties"]

            # Contact name (Title)
            title = props["Contact"]["title"]
            contact_name = title[0]["plain_text"] if title else "there"

            # Email address
            email_addr = props["Email"].get("email")
            if not email_addr:
                raise ValueError("Missing email address")

            log(f"Sending email to {contact_name} <{email_addr}>")

            # Email message
            msg = EmailMessage()
            msg["Subject"] = "GLOBALMIX launches in Tulum — Join the network"
            msg["From"] = EMAIL_USER
            msg["To"] = email_addr

            msg.set_content(
                f"Hi {contact_name},\n\n"
                "GLOBALMIX has officially launched in Tulum.\n\n"
                "Join the network here:\n"
                "https://www.globalmix.online\n\n"
                "— MIAMIX"
            )

            smtp.send_message(msg)
            log(f"✅ Email sent to {email_addr}")

            # Update Notion: Status → Sent, Send Email → No
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Status": {
                        "status": {"name": "Sent"}
                    },
                    "Send Email": {
                        "select": {"name": "No"}
                    }
                }
            )

            log(f"🔄 Notion updated → Sent / Send Email = No ({contact_name})")

        except Exception as e:
            log(f"❌ ROW ERROR ({page.get('id')}): {e}")

    smtp.quit()
    log("--- SCRIPT COMPLETE ---")


if __name__ == "__main__":
    main()