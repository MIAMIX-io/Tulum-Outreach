import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

# 1. Initialize Clients
notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    # 2. Query Notion for contacts where Status is "Ready to Send"
    # Note: Make sure you have an option in your Status column named "Ready to Send"
    results = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Status",
            "status": {"equals": "Ready to Send"} # Using 'status' type filter
        }
    ).get("results")

    if not results:
        print("No contacts found with status 'Ready to Send'.")
        return

    # 3. Connect to Gmail SMTP
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
    except Exception as e:
        print(f"Failed to connect to email: {e}")
        return

    for page in results:
        try:
            # Extract data using your specific column names
            email_addr = page["properties"]["Email"]["email"]
            # 'Contact' is your 'Title' column
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            page_id = page["id"]

            if not email_addr:
                print(f"Skipping {contact_name}: No email address found.")
                continue

            # Compose Email
            msg = EmailMessage()
            msg['Subject'] = "Follow up: Tulum Project"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name},\n\nThis is an automated message regarding the Tulum Project.")
            
            smtp.send_message(msg)
            print(f"Email sent to {email_addr}")

            # 4. Update Status to "Sent" (This acts as your 'webhook' update)
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"status": {"name": "Sent"}}
                }
            )
            print(f"Status updated to 'Sent' for {contact_name}")

        except Exception as e:
            print(f"Error processing {page_id}: {e}")

    smtp.quit()

if __name__ == "__main__":
    main()
