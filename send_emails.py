import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

# 1. Initialize Clients
notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    # 2. Query Notion for contacts where Status is "Ready to Send"
    # Note: Ensure the status option is exactly "Ready to Send" in Notion
    try:
        results = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Status",
                "status": {"equals": "Ready to Send"}
            }
        ).get("results")
    except Exception as e:
        print(f"Error querying Notion: {e}")
        return

    if not results:
        print("No contacts found with status 'Ready to Send'.")
        return

    # 3. Connect to Gmail SMTP
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
    except Exception as e:
        print(f"Gmail Login Failed: {e}. Check your App Password.")
        return

    for page in results:
        try:
            # Mapping based on your CSV: Contact (Title) and Email (Email)
            email_addr = page["properties"]["Email"]["email"]
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            page_id = page["id"]

            if not email_addr:
                print(f"Skipping {contact_name}: No email address.")
                continue

            # Compose Email
            msg = EmailMessage()
            msg['Subject'] = "Follow up: Tulum Project"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name},\n\nThis is an automated update regarding the Tulum Project.")
            
            smtp.send_message(msg)
            print(f"✅ Email sent to {email_addr}")

            # 4. Update Status to "Sent" (Acting as your confirmation webhook)
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"status": {"name": "Sent"}}
                }
            )
            print(f"🔄 Status updated to 'Sent' for {contact_name}")

        except Exception as e:
            print(f"Error processing {contact_name}: {e}")

    smtp.quit()

if __name__ == "__main__":
    main()
