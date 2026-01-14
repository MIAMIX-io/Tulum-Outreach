import os
import smtplib
from email.message import EmailMessage
from notion_client import Client

# 1. Initialize Clients
notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def main():
    # 2. Query Notion for contacts with status 'To Send'
    results = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Status",
            "select": {"equals": "To Send"}
        }
    ).get("results")

    if not results:
        print("No contacts found to email.")
        return

    # 3. Connect to SMTP (Gmail example)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])

        for page in results:
            email_addr = page["properties"]["Email"]["email"]
            name = page["properties"]["Name"]["title"][0]["plain_text"]
            page_id = page["id"]

            # Send Email
            msg = EmailMessage()
            msg['Subject'] = "Your Triggered Update"
            msg['From'] = os.environ["EMAIL_USER"]
            msg['To'] = email_addr
            msg.set_content(f"Hi {name}, this is an automated update!")
            smtp.send_message(msg)

            # 4. Update Notion Status (Acting as your 'webhook' logic)
            notion.pages.update(
                page_id=page_id,
                properties={"Status": {"select": {"name": "Sent"}}}
            )
            print(f"Sent and updated: {email_addr}")

if __name__ == "__main__":
    main()
