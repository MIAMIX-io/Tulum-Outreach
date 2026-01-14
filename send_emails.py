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

    # ── ENV VARS ─────────────────────────────────────────────
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        raise RuntimeError("❌ Missing required environment variables")

    # ── NOTION CLIENT ───────────────────────────────────────
    notion = Client(auth=NOTION_TOKEN)

    log("🔍 Querying Notion database...")

    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "and": [
                    {
                        "property": "Status",
                        "status": {
                            "equals": "Ready to Send"
                        }
                    },
                    {
                        "property": "Send Email",
                        "select": {
                            "equals": "Yes"
                        }
                    }
                ]
            }
        )
        pages = response.get("results", [])
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    log(f"📬 Emails queued: {len(pages)}")
    if not pages:
        return

    # ── SMTP ────────────────────────────────────────────────
    log("🔐 Connecting to Gmail SMTP...")
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    log("✅ SMTP authenticated")

    # ── TEMPLATE ENGINE ─────────────────────────────────────
    env = Environment(loader=FileSystemLoader("emails"))
    wrapper = env.get_template("email_template.html")

    with open("emails/OutreachTulum-20260113.html", "r", encoding="utf-8") as f:
        outreach_html = f.read()

    # ── SEND LOOP ───────────────────────────────────────────
    for page in pages:
        try:
            props = page["properties"]

            # Contact name (Title property)
            title = props["Contact"]["title"]
            name = title[0]["plain_text"] if title else "there"

            # Email
            email = props["Email"]["email"]
            if
