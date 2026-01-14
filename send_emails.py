import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    print("Connecting to Notion...")
    
    # This filter looks specifically for the name of the status
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

    print(f"Found {len(results)} contacts ready to email.")

    if not results:
        print("Check: Is the status name EXACTLY 'Ready to Send' (case sensitive)?")
        return

    # Gmail Connection
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
    except Exception as e:
        print(f"Gmail Login Error: {e}")
        return

    for page in results:
        try:
            # Using 'Contact' for name and 'Email' for address per your CSV
            contact_name = page["properties"]["Contact"]["title"][0]["plain_text"]
            email_addr = page["properties"]["Email"]["email"]
            page_id = page["id"]

            print(f"Sending to: {contact_name}...")

            msg = EmailMessage()
            msg['Subject'] = "Tulum Project Follow-up"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {contact_name},\n\nThis is the automated test for the Tulum Project.")
            
            smtp.send_message(msg)
            
            # Update status to 'Sent' (which you put in the 'Complete' group)
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {
                            "name": "Sent"
                        }
                    }
                }
            )
            print(f"Done: {contact_name} moved to Sent.")

        except Exception as e:
            print(f"Error processing a row: {e}")

    smtp.quit()
    print("Workflow complete.")

if __name__ == "__main__":
    main()
