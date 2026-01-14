import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from notion_client import Client
from jinja2 import Environment, FileSystemLoader


def log(message):
    print(message, flush=True)


def main():
    log("🚀 SCRIPT INITIALIZING")

    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not NOTION_TOKEN or not DATABASE_ID:
        raise RuntimeError("Missing Notion configuration")

    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise RuntimeError("Missing email credentials")

    notion = Client(auth=NOTION_TOKEN)

    log("🔍 Querying Notion database")

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
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    pages = response.get("results", [])
    log(f"📬 Found {len(pages)} records")

    if not pages:
        return

    log("🔐 Connecting to Gmail SMTP")
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)

    env = Environment(loader=FileSystemLoader("emails"))
    template = env.get_template("email_template.html")

    with open("emails/OutreachTulum-20260113.html", "r", encoding="utf-8") as f:
        outreach_html = f.read()

    for page in pages:
        try:
            props = page["properties"]

            title = props["Contact"]["title"]
            name = title[0]["plain_text"] if title else "there"

            email = props["Email"]["email"]
            if not email:
                raise ValueError("Missing email address")

            log(f"➡ Sending to {name} <{email}>")

            html = template.render(
                newsletter_title="GLOBALMIX launches in Tulum — Join the network",
                name=name,
                background_color="#F5F5F5",
                brand_color="#E136C4",
                email_content_from_file=outreach_html
            )

            msg = EmailMessage()
            msg["Subject"] = "GLOBALMIX launches in Tulum — Join the network"
            msg["From"] = formataddr(("MIAMIX", "no-reply@miamix.io"))
            msg["To"] = email
            msg["Reply-To"] = "info@miamix.io"

            msg.set_content(
                f"Hi {name},\n\n"
                "Please view this email in HTML format.\n\n"
                "MIAMIX"
            )

            msg.add_alternative(html, subtype="html")
            smtp.send_message(msg)

            log("✅ Email sent")

            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Status": {"status": {"name": "Sent"}},
                    "Send Email": {"select": {"name": "No"}}
                }
            )

            log("🔄 Notion updated")

        except Exception as e:
            log(f"❌ ROW ERROR: {e}")

    smtp.quit()
    log("🏁 SCRIPT COMPLETE")


if __name__ == "__main__":
    main()
