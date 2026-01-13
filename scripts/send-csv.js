/* scripts/send-csv.js */
/* eslint-disable no-console */
const fs = require("fs");
const path = require("path");
const https = require("https");
const { parse } = require("csv-parse/sync");
const nodemailer = require("nodemailer");

function env(name, required = true) {
  const v = process.env[name];
  if (required && (!v || v.trim() === "")) throw new Error(`Missing env ${name}`);
  return v.trim();
}

async function fetchText(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode}`));
      let data = "";
      res.on("data", (d) => (data += d));
      res.on("end", () => resolve(data));
    }).on("error", reject);
  });
}

(async () => {
  // Inputs
  const CATEGORY = env("CATEGORY");  // travel | sports | fashion | arts | hospitality | wellness | intermiami
  const YEAR = env("YEAR");          // "2025"
  const MONTH = env("MONTH");        // "10"
  const SHEET_CSV_URL = env("SHEET_CSV_URL");

  // SMTP
  const SMTP_HOST = env("SMTP_HOST");
  const SMTP_PORT = Number(env("SMTP_PORT") || 587);
  const SMTP_USER = process.env.SMTP_USER || ""; // allow empty for IP-allowlist relays
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

  // Subject
  const monthYear = new Date(`${YEAR}-${MONTH}-01T00:00:00Z`)
    .toLocaleString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
  const SUBJECT = cat.subject.replace("{MONTH_YEAR}", monthYear);

  // HTML
  const htmlPath = cat.path.replace("{YEAR}", YEAR).replace("{MONTH}", MONTH);
  if (!fs.existsSync(htmlPath)) throw new Error(`HTML not found: ${htmlPath}`);
  const HTML = fs.readFileSync(htmlPath, "utf8");

  // Fetch and parse CSV (expects headers: Email, First Name, Consent Timestamp, Segment, Status)
  const csvText = await fetchText(SHEET_CSV_URL);
  const rows = parse(csvText, { columns: true, skip_empty_lines: true });

  const recipients = rows
    .filter(r =>
      String(r.Segment || "").trim() === cat.segment &&
      String(r.Status || "").trim().toLowerCase() === "active" &&
      String(r.Email || "").includes("@")
    )
    .map(r => ({
      email: String(r.Email || "").trim(),
      first: String(r["First Name"] || "").trim()
    }));

  // SMTP transport
  const transportOpts = { host: SMTP_HOST, port: SMTP_PORT, secure: false };
  if (SMTP_USER && SMTP_PASS) transportOpts.auth = { user: SMTP_USER, pass: SMTP_PASS };
  const transporter = nodemailer.createTransport(transportOpts);

  const headers = {
    "List-Unsubscribe": "<mailto:unsubscribe@miamix.io>",
    "X-Campaign-Category": cat.segment,
    "X-Campaign-Month": `${YEAR}-${MONTH}`
  };

  const delay = (ms) => new Promise(r => setTimeout(r, ms));
  const results = { total: recipients.length, sent: 0, failed: 0, sample: [], errors: [] };

  for (const r of recipients) {
    try {
      const info = await transporter.sendMail({
        from: SMTP_FROM,
        to: r.email,
        subject: SUBJECT,
        html: HTML,
        headers
      });
      results.sent += 1;
      if (results.sample.length < 5) results.sample.push({ to: r.email, id: info.messageId || "" });
      await delay(100); // light throttle
    } catch (e) {
      results.failed += 1;
      results.errors.push({ to: r.email, error: e.message });
    }
  }

  fs.writeFileSync("run-log.json", JSON.stringify({
    category: CATEGORY, year: YEAR, month: MONTH,
    subject: SUBJECT, htmlPath, totals: results, ts: new Date().toISOString()
  }, null, 2));

  console.log(`Done. Category=${CATEGORY} Recipients=${results.total} Sent=${results.sent} Failed=${results.failed}`);
})().catch(err => { console.error(err); process.exit(1); });
