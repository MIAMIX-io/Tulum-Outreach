import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

def main():
    # 1. Setup Clients
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")
    notion = Client(auth=token)

    print("Checking Notion for contacts...")

    # 2. Query for 'Ready to Send'
    try:
        response = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Status",
                "status": {"equals": "Ready to Send"}
            }
        )
        results = response.get("results", [])
    except Exception as e:
        print(f"Error querying Notion: {e}")
        return

    if not results:
        print("No contacts found with status 'Ready to Send'.")
        return

    print(f"Found {len(results)} contact(s). Connecting to email...")

    # 3. Connect to Gmail
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
    except Exception as e:
        print(f"Gmail Login Failed: {e}")
        return

    # 4. Process Each Contact
    for page in results:
        try:
            # Matches your CSV: 'Contact' (Name) and 'Email'
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            email_addr = page["properties"]["Email"]["email"]
            page_id = page["id"]

            print(f"Sending to {contact_name} ({email_addr})...")

            msg = EmailMessage()
            msg['Subject'] = "Tulum Project Follow-up"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name},\n\nThis is an automated update regarding the Tulum Project.")
            
            smtp.send_message(msg)

            # 5. Update Status to 'Sent'
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"status": {"name": "Sent"}}
                }
            )
            print(f"✅ Successfully sent and updated {contact_name}")

        except Exception as e:
            print(f"❌ Error processing {page_id}: {e}")

    smtp.quit()
    print("Workflow finished.")

if __name__ == "__main__":
    main()
