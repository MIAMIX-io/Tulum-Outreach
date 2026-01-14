import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    print("Connecting to Notion...")
    
    # Updated query: Using a more general filter to catch the 'Ready to Send' tag
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
        print(f"Error: Database query failed. {e}")
        return

    print(f"DEBUG: Found {len(results)} rows with status 'Ready to Send'.")

    if not results:
        print("Stopping: No contacts found to process. Please check that a row is set to 'Ready to Send'.")
        return

    # Connect to Email
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
        print("DEBUG: Gmail login successful.")
    except Exception as e:
        print(f"DEBUG: Gmail login failed: {e}")
        return

    for page in results:
        contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
        email_addr = page["properties"]["Email"]["email"]
        page_id = page["id"]

        print(f"Processing: {contact_name} <{email_addr}>")

        msg = EmailMessage()
        msg['Subject'] = "Follow up: Tulum Project"
        msg['From'] = os.environ["EMAIL_USER"]
        msg['To'] = email_addr
        msg.set_content(f"Hi {contact_name},\n\nThis is an automated test for the Tulum Project.")
        
        smtp.send_message(msg)
        print(f"✅ Email sent to {contact_name}")

        # Update Notion Status to 'Sent'
        notion.pages.update(
            page_id=page_id,
            properties={"Status": {"status": {"name": "Sent"}}}
        )
        print(f"🔄 Notion updated to 'Sent' for {contact_name}")

    smtp.quit()

if __name__ == "__main__":
    main()
