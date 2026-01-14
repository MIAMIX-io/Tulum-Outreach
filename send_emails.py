import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from notion_client import Client
from jinja2 import Environment, FileSystemLoader


def log(msg):
    print(msg, flush=True)


def main():
    log("🚀 SCRIPT INITIALIZING")

    # --- ENV ---
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        raise RuntimeError("❌ Missing required environment variables")

    notion = Client(auth=NOTION_TOKEN)

    # --- QUERY NOTION ---
    log("🔍 Querying Notion database...")

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
        rows = response.get("results", [])
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    log(f"📬 Rows ready to send: {len(rows)}")
    if not rows:
        return

    # --- SMTP ---
    log("🔐 Connecting to Gmail SMTP...")
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    log("✅ SMTP authenticated")

    # --- TEMPLATE SETUP ---
    env = Environment(loader=FileSystemLoader("emails"))
    wrapper = env.get_template("email_template.html")
    outreach_html = open("emails/OutreachTulum-20260113.html", "r", encoding="utf-8").read()

    # --- SEND LOOP ---
    for page in rows:
        try:
            props = page["properties"]

            # Contact name
            title = props["Contact"]["title"]
            name = title[0]["plain_text"] if title else "there"

            # Email
            email = props["Email"]["email"]
            if not email:
                raise ValueError("Missing email")

            log(f"➡ Sending to {name} <{email}>")

            html_body = wrapper.render(
                newsletter_title="GLOBALMIX launches in Tulum — Join the network",
                name=name,
                background_color="#F5F5F5",
                brand_color="#E136C4",
                email_content_from_file=outreach_html,
            )

            msg = EmailMessage()
            msg["Subject"] = "GLOBALMIX launches in Tulum — Join the network"
            msg["From"] = formataddr(("MIAMIX", "no-reply@miamix.io"))
            msg["To"] = email
            msg["Reply-To"] = "info@miamix.io"

            msg.set_content(
                f"Hi {name},\n\n"
                "Please view this email in HTML.\n\n"
                "MIAMIX"
            )

            msg.add_alternative(html_body, subtype="html")

            smtp.send_message(msg)
            log("✅ Sent")

            # --- UPDATE NOTION ---
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "St
