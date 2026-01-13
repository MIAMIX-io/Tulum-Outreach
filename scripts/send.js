// scripts/send.js

/ *eslint-disable no-console* /

const fs = require("fs");

const path = require("path");

const nodemailer = require("nodemailer");

const { GoogleAuth } = require("google-auth-library");

const { google } = require("googleapis");

function env(name, required = true) {

const v = process.env[name];

if (required && (!v || v.trim() === "")) throw new Error(`Missing env ${name}`);

return v.trim();

}

(async () => {

// Inputs from workflow

const CATEGORY = env("CATEGORY");          // travel | sports | fashion | arts | hospitality | wellness | intermiami

const YEAR = env("YEAR");                  // "2025"

const MONTH = env("MONTH");                // "10"

const SHEET_ID = env("SHEET_ID");          // Master sheet ID

// SMTP

const SMTP_HOST = env("SMTP_HOST");

const SMTP_PORT = Number(env("SMTP_PORT") || 587);

const SMTP_USER = process.env.SMTP_USER || ""; // allow empty for IP-allowlist

const SMTP_PASS = process.env.SMTP_PASS || "";

const SMTP_FROM = env("SMTP_FROM");

// Category mapping

const mapping = {

travel:      { segment: "Travel",            subject: "MIAMIX Travel Guide, {MONTH_YEAR}, [Article Title]",       path: "emails/travel/{YEAR}-{MONTH}.html" },

sports:      { segment: "Sports",            subject: "MIAMIX Sports Updates, {MONTH_YEAR}, [Article Title]",     path: "emails/sports/{YEAR}-{MONTH}.html" },

fashion:     { segment: "Fashion",           subject: "MIAMIX Fashion, {MONTH_YEAR} Edition, [Article Title]",    path: "emails/fashion/{YEAR}-{MONTH}.html" },

arts:        { segment: "Arts & Culture",    subject: "MIAMIX Culture & Arts, {MONTH_YEAR}, Spotlight, [Article Title]", path: "emails/arts/{YEAR}-{MONTH}.html" },

hospitality: { segment: "Hospitality",       subject: "MIAMIX Hospitality Review, {MONTH_YEAR}, [Article Title]", path: "emails/hospitality/{YEAR}-{MONTH}.html" },

wellness:    { segment: "Health & Wellness", subject: "MIAMIX Health & Wellness Journal, {MONTH_YEAR}, [Article Title]", path: "emails/wellness/{YEAR}-{MONTH}.html" },

intermiami:  { segment: "Inter Miami",       subject: "MIAMIX The Inter Circle, {MONTH_YEAR} Brief, [Article Title]", path: "emails/intermiami/{YEAR}-{MONTH}.html" }

};

const cat = mapping[CATEGORY];

if (!cat) throw new Error(`Unknown CATEGORY: ${CATEGORY}`);

// Subject month formatting (UTC so cron alignment is predictable)

const monthYear = new Date(`${YEAR}-${MONTH}-01T00:00:00Z`)

.toLocaleString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });

const SUBJECT = cat.subject.replace("{MONTH_YEAR}", monthYear);

const htmlPath = cat.path.replace("{YEAR}", YEAR).replace("{MONTH}", MONTH);

if (!fs.existsSync(htmlPath)) throw new Error(`HTML not found: ${htmlPath}`);

const HTML = fs.readFileSync(htmlPath, "utf8");

// Google Sheets auth via OIDC/ADC

const auth = new GoogleAuth({ scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"] });

const client = await auth.getClient();

const sheets = google.sheets({ version: "v4", auth: client });

// Read Master: A Email, B First Name, C Consent, D Segment, E Status

const res = await sheets.spreadsheets.values.get({ spreadsheetId: SHEET_ID, range: "Master!A:E" });

const rows = [res.data](http://res.data).values || [];

const header = rows[0] || [];

const idx = {

email:    header.indexOf("Email"),

first:    header.indexOf("First Name"),

segment:  header.indexOf("Segment"),

status:   header.indexOf("Status")

};

if ([idx.email](http://idx.email) < 0 || idx.segment < 0 || idx.status < 0) {

throw new Error("Master missing required headers: Email, Segment, Status");

}

const recipients = rows.slice(1).filter(r =>

(r[idx.segment] || "").trim() === cat.segment &&

(r[idx.status]  || "").trim().toLowerCase() === "active" &&

(r[[idx.email](http://idx.email)]   || "").includes("@")

).map(r => ({

email: (r[[idx.email](http://idx.email)] || "").trim(),

first: idx.first >= 0 ? (r[idx.first] || "").trim() : ""

}));

// SMTP transport

const transportOpts = { host: SMTP_HOST, port: SMTP_PORT, secure: false };

if (SMTP_USER && SMTP_PASS) transportOpts.auth = { user: SMTP_USER, pass: SMTP_PASS };

const transporter = nodemailer.createTransport(transportOpts);

const headers = {

"List-Unsubscribe": "<[mailto:unsubscribe@miamix.io](mailto:unsubscribe@miamix.io)>",

"X-Campaign-Category": cat.segment,

"X-Campaign-Month": `${YEAR}-${MONTH}`

};

const delay = ms => new Promise(r => setTimeout(r, ms));

const results = { total: recipients.length, sent: 0, failed: 0, sample: [], errors: [] };

for (const r of recipients) {

try {

const info = await transporter.sendMail({

from: SMTP_FROM,

to: [r.email](http://r.email),

subject: SUBJECT,

html: HTML,

headers

});

results.sent += 1;

if (results.sample.length < 5) results.sample.push({ to: [r.email](http://r.email), id: info.messageId || "" });

await delay(100);

} catch (e) {

results.failed += 1;

results.errors.push({ to: [r.email](http://r.email), error: e.message });

}

}

fs.writeFileSync("run-log.json", JSON.stringify({

category: CATEGORY, year: YEAR, month: MONTH,

subject: SUBJECT, htmlPath, totals: results, ts: new Date().toISOString()

}, null, 2));

console.log(`Done. Category=${CATEGORY} Recipients=${[results.total](http://results.total)} Sent=${results.sent} Failed=${results.failed}`);

})().catch(err => { console.error(err); process.exit(1); });
