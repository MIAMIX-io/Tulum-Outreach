import os
import smtplib
import requests
from email.message import EmailMessage
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def log(msg):
    print(msg, flush=True)


def notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def main():
    log("🚀 SCRIPT INITIALIZING")

    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        raise RuntimeError("❌ Missing required environment variables")

    # --- Query Notion (RAW API) ---
    log("🔍 Querying Notion database")

    query_payload = {
        "filter": {
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
    }

    res = requests.post(
        f"{NOTION_API}/databases/{DATABASE_ID}/query",
        headers=notion_headers(NOTION_TOKEN),
        json=query_payload,
        timeout=30
    )

    if not res.ok:
        raise RuntimeError(f"❌ Notion query failed: {res.text}")

    pages = res.json().get("results", [])
    log(f"📬 Found {len(pages)} contacts")

    if not pages:
        return

    # --- Email setup ---
    log("🔐 Connecting to Gmail SMTP")
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)

    env = Environment(loader=FileSystemLoader("emails"))
    template = env.get_template("email_template.html")

    with open("emails/OutreachTulum-20260113.html", encoding="utf-8") as f:
        outreach_html = f.read()

    for page in pages:
        try:
            props = page["properties"]

            title = props["Contact"]["title"]
            name = title[0]["plain_text"] if title else "there"

            email = props["Email"]["email"]
            if not email:
                raise ValueError("Missing email")

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

            msg.set_content(f"Hi {name}, please view this email in HTML format.")
            msg.add_alternative(html, subtype="html")

            smtp.send_message(msg)
            log("✅ Email sent")

            # --- Update Notion ---
            update_payload = {
                "properties": {
                    "Status": {"status": {"name": "Sent"}},
                    "Send Email": {"select": {"name": "No"}}
                }
            }

            upd = requests.patch(
                f"{NOTION_API}/pages/{page['id']}",
                headers=notion_headers(NOTION_TOKEN),
                json=update_payload,
                timeout=30
            )

            if not upd.ok:
                log(f"⚠ Notion update failed: {upd.text}")
            else:
                log("🔄 Notion updated")

        except Exception as e:
            log(f"❌ ROW ERROR: {e}")

    smtp.quit()
    log("🏁 SCRIPT COMPLETE")


if __name__ == "__main__":
    main()
