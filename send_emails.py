import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from notion_client import Client
from jinja2 import Environment, FileSystemLoader


# -----------------------------
# Logging helper
# -----------------------------
def log(msg):
    print(msg, flush=True)


# -----------------------------
# Main
# -----------------------------
def main():
    log("🚀 SCRIPT INITIALIZING")

    # -----------------------------
    # Load environment variables
    # -----------------------------
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not all([NOTION_TOKEN, DATABASE_ID, EMAIL_USER, EMAIL_PASSWORD]):
        raise RuntimeError("❌ Missing required environment variables")

    # -----------------------------
    # Init Notion client
    # -----------------------------
    notion = Client(auth=NOTION_TOKEN)

    # Explicit SDK sanity check
    if not callable(getattr(notion.databases, "query", None)):
        raise RuntimeError("❌ Broken Notion SDK detected")

    # -----------------------------
    # Query Notion (Send Email = Yes)
    # -----------------------------
    log("🔍 Querying Notion database...")

    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Send Email",
                "select": {"equals": "Yes"}
            }
        )
    except Exception as e:
        raise RuntimeError(f"❌ NOTION API ERROR: {e}")

    pages = response.get("results", [])
    log(f"📄 Found {len(pages)} records ready to send")

    if not pages:
        log("✅ Nothing to send. Exiting.")
        return

    # -----------------------------
    # Load email templates
    # -----------------------------
    env = Environment(loader=FileSystemLoader("emails"))

    base_template = env.get_template("email_template.html")
    outreach_html = open(
        "emails/OutreachTulum-20260113.html",
        encoding="utf-8"
    ).read()

    # -----------------------------
    # SMTP setup (Gmail)
    # -----------------------------
    log("📨 Connecting to Gmail SMTP...")
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    except Exception as e:
        raise RuntimeError(f"❌ EMAIL LOGIN ERROR: {e}")

    log("✅ SMTP connected")

    # -----------------------------
    # Send emails
    # -----------------------------
    for page in pages:
        page_id = page["id"]
        props = page["properties"]

        try:
            # ---- Contact name (Title)
            title_items = props["Contact"]["title"]
            contact_name = (
                title_items[0]["plain_text"]
                if title_items else "there"
            )

            # ---- Email
            email_addr = props["Email"]["email"]
            if not email_addr:
                raise ValueError("Missing Email")

            log(f"➡️ Sending to {contact_name} <{email_addr}>")

            # ---- Render HTML
            html_body = base_template.render(
                newsletter_title="GLOBALMIX launches in Tulum — Join the network",
                name=contact_name,
                background_color="#F5F5F5",
                brand_color="#E136C4",
                email_content_from_file=outreach_html,
                custom_message=None
            )

            # ---- Build email
            msg = EmailMessage()
            msg["Subject"] = "GLOBALMIX launches in Tulum — Join the network"
            msg["From"] = formataddr(("MIAMIX", "no-reply@miamix.io"))
            msg["To"] = email_addr
            msg["Reply-To"] = "info@miamix.io"

            msg.set_content(
                f"Hi {contact_name},\n\n"
                "Please view this email in HTML format.\n\n"
                "MIAMIX"
            )

            msg.add_alternative(html_body, subtype="html")

            # ---- Send
            smtp.send_message(msg)
            log(f"✅ Sent to {email_addr}")

            # ---- Update Notion
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Send Email": {"select": {"name": "No"}},
                    "Status": {"select": {"name": "Sent"}}
                }
            )

            log(f"🔄 Notion updated for {contact_name}")

        except Exception as e:
            log(f"❌ ERROR ({page_id}): {e}")

    smtp.quit()
    log("🎉 SCRIPT COMPLETE")


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    main()
