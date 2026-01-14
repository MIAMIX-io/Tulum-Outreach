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

    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if NOTION_TOKEN is None or DATABASE_ID is None:
        raise RuntimeError("Missing Notion environment variables")

    if EMAIL_USER is None or EMAIL_PASSWORD is None:
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
    except Exception as e:
        log(f"❌ NOTION API ERROR: {e}")
        return

    pages = response.get("results", [])
    log(f"📬 Found {len(pages)} records")

    if len(pages) == 0:
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
            name = title[0]["plain_text"] if title else "there_]()
