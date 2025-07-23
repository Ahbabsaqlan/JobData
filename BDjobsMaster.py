#!/usr/bin/env python3
import os
import ast
import time
import smtplib
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ================= CONFIGURATION ================= #

# ✅ Always use absolute paths
BASE_DIR = "/Users/jihan/JobData"  # <-- change this if you move script

PAGES_TO_SCRAPE = 3
JOBS_PER_PAGE = 10
API_URL_TEMPLATE = "https://gateway.bdjobs.com/ActtivejobsTest/api/JobSubsystem/jobDetails?jobId={}"
REQUEST_DELAY = 0.3

MASTER_FILE = os.path.join(BASE_DIR, "bdjobs_master_data.xlsx")  # ✅ Full path
LOG_DIR = os.path.join(BASE_DIR, "logs")  # ✅ Full path

# ✅ Email Alert Config
ENABLE_EMAIL_ALERTS = True
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "ahbabzami3@gmail.com"
EMAIL_PASSWORD = "**** **** **** ****"  # Gmail App Password
EMAIL_RECEIVERS = [
    "22-48108-2@student.aiub.edu",
    "22-48091-2@student.aiub.edu"
]

# ✅ Setup Logging
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = datetime.now().strftime("run_%Y-%m-%d_%H-%M.log")
log_path = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# ================= EMAIL FUNCTION ================= #
def send_email(subject, body):
    if not ENABLE_EMAIL_ALERTS:
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(EMAIL_RECEIVERS)  # show all in email header
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(
                EMAIL_SENDER,
                EMAIL_RECEIVERS,  # send to all
                msg.as_string()
            )

        logging.info(f"📧 Email sent to: {', '.join(EMAIL_RECEIVERS)}")
    except Exception as e:
        logging.error(f"❌ Failed to send email alert: {e}")


# ================= HELPER FUNCTIONS ================= #
def extract_list_from_html(raw_html):
    if not raw_html:
        return []
    soup = BeautifulSoup(raw_html, "html.parser")
    items = [li.get_text(strip=True) for li in soup.find_all(["li", "p"])]
    return items if items else [soup.get_text(strip=True)]

def fetch_job_details_from_api(job_id):
    url = API_URL_TEMPLATE.format(job_id)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logging.warning(f"❌ Failed to fetch job {job_id}, HTTP {resp.status_code}")
            return None
        
        data = resp.json()
        if data.get("statuscode") != "0" or not data.get("data"):
            logging.warning(f"⚠️ No valid data for job {job_id}")
            return None
        
        job = data["data"][0]
        
        return {
            "Job ID": str(job.get("JobId")),  # ✅ Force string for consistency
            "Job Title": job.get("JobTitle"),
            "Company Name": job.get("CompnayName"),
            "Posted On": job.get("PostedOn"),
            "Deadline": job.get("Deadline"),
            "Vacancies": job.get("JobVacancies"),
            "Job Nature": job.get("JobNature"),
            "Workplace": job.get("JobWorkPlace"),
            "Education Requirements": extract_list_from_html(job.get("EducationRequirements")),
            "Experience": extract_list_from_html(job.get("experience")),
            "Additional Requirements": extract_list_from_html(job.get("AdditionJobRequirements")),
            "Skills Required": [s.strip() for s in job.get("SkillsRequired", "").split(",") if s.strip()],
            "Job Description": extract_list_from_html(job.get("JobDescription")),
            "Location": job.get("JobLocation"),
            "Salary Range": job.get("JobSalaryRange"),
            "Company Address": job.get("CompanyAddress"),
            "Apply Email": job.get("ApplyEmail"),
            "Apply Instruction": BeautifulSoup(job.get("ApplyInstruction") or "", "html.parser").get_text(strip=True),
            "Job Link": f"https://jobs.bdjobs.com/jobdetails.asp?id={job_id}"
        }
    except Exception as e:
        logging.error(f"❌ Error fetching job {job_id}: {e}")
        return None

def load_existing_job_ids():
    """Load existing Job IDs safely. Returns a set of IDs (as strings)."""
    if not os.path.exists(MASTER_FILE):
        logging.warning(f"⚠️ Master file not found: {MASTER_FILE}")
        return set()
    try:
        df = pd.read_excel(MASTER_FILE, engine="openpyxl")
        # ✅ Force all to string for consistent comparison
        return set(df["Job ID"].astype(str).tolist())
    except Exception as e:
        logging.error(f"❌ Could not read master file: {e}")
        return set()

def save_to_master(new_data):
    """Merge new scraped data into master file safely."""
    df_new = pd.DataFrame(new_data)
    list_cols = ["Education Requirements", "Experience", "Additional Requirements", "Skills Required", "Job Description"]
    
    for col in list_cols:
        if col in df_new.columns:
            df_new[col] = df_new[col].apply(lambda x: "; ".join(x) if isinstance(x, list) else x)
    
    if os.path.exists(MASTER_FILE):
        try:
            df_old = pd.read_excel(MASTER_FILE, engine="openpyxl")
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["Job ID"], keep="last", inplace=True)
            df_combined.to_excel(MASTER_FILE, index=False, engine="openpyxl")
            logging.info(f"✅ Merged into master. Total unique jobs: {len(df_combined)}")
        except Exception as e:
            logging.error(f"❌ Failed merging into master: {e}")
            # ✅ Backup new data separately if merge fails
            backup_file = os.path.join(BASE_DIR, f"backup_new_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
            df_new.to_excel(backup_file, index=False, engine="openpyxl")
            logging.warning(f"🆘 Saved new data separately as backup: {backup_file}")
            send_email("Bdjobs Scraper: Merge Failed ❌", f"Merge failed. Backup saved at:\n{backup_file}")
    else:
        # ✅ If no master exists, create it safely
        df_new.to_excel(MASTER_FILE, index=False, engine="openpyxl")
        logging.info(f"✅ Created new master file with {len(df_new)} jobs.")

# ================= MAIN SCRAPER LOGIC ================= #
def main():
    logging.info("🚀 Scraper started")

    # STEP 1: Collect job IDs
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    job_ids = []

    try:
        logging.info(f"--- Collecting Job IDs from {PAGES_TO_SCRAPE} pages ---")
        for page_num in range(1, PAGES_TO_SCRAPE + 1):
            try:
                url = f"https://jobs.bdjobs.com/jobsearch.asp?pg={page_num}&rpp={JOBS_PER_PAGE}"
                driver.get(url)
                element = driver.find_element("id", "arrTempJobIds")
                job_ids_value = element.get_attribute("value")
                ids_on_page = ast.literal_eval(job_ids_value)
                job_ids.extend(ids_on_page)
                logging.info(f"✅ Page {page_num}: Found {len(ids_on_page)} job IDs. Total: {len(job_ids)}")
            except TimeoutException:
                logging.warning(f"⚠️ Timeout on page {page_num}, skipping.")
            except Exception as e:
                logging.error(f"❌ Error on page {page_num}: {e}")
    finally:
        driver.quit()
        logging.info("--- Finished ID collection ---")

    # ✅ Deduplicate collected IDs
    job_ids = list(set(job_ids))
    logging.info(f"🔎 Total unique IDs collected: {len(job_ids)}")

    # STEP 2: Filter already scraped (strict string match)
    existing_ids = load_existing_job_ids()

    # ✅ Force all IDs to strings for consistent comparison
    job_ids = [str(jid) for jid in job_ids]
    existing_ids = {str(eid) for eid in existing_ids}

    new_job_ids = [jid for jid in job_ids if jid not in existing_ids]

    logging.info(f"📂 Existing jobs in master: {len(existing_ids)}")
    logging.info(f"🆕 New jobs to scrape: {len(new_job_ids)}")

    # ✅ Log how many got filtered
    if len(new_job_ids) < len(job_ids):
        logging.info(f"✅ Filtered out {len(job_ids) - len(new_job_ids)} already-scraped jobs.")
    else:
        logging.warning("⚠️ No filtering happened – possible master file mismatch?")

    if not new_job_ids:
        msg = "✅ No new jobs found. Scraper finished."
        logging.info(msg)
        send_email("Bdjobs Scraper: No new jobs ✅", msg)
        return

    # STEP 3: Scrape new job details
    scraped_data = []
    for i, job_id in enumerate(new_job_ids, 1):
        job_details = fetch_job_details_from_api(job_id)
        if job_details:
            scraped_data.append(job_details)
            logging.info(f"✅ Scraped {i}/{len(new_job_ids)}: {job_details['Job Title']}")
        time.sleep(REQUEST_DELAY)

    # STEP 4: Merge into master
    if scraped_data:
        save_to_master(scraped_data)
        summary_msg = f"✅ Scraper completed.\n\nNew jobs scraped: {len(scraped_data)}\nTotal master jobs: {len(existing_ids) + len(scraped_data)}"
        send_email("Bdjobs Scraper: Completed ✅", summary_msg)
    else:
        warning_msg = "⚠️ Scraper ran but no job details were scraped."
        logging.warning(warning_msg)
        send_email("Bdjobs Scraper: Warning ⚠️", warning_msg)

    logging.info("🏁 Scraper finished successfully.")

# ================= RUN WITH GLOBAL CRASH HANDLER ================= #
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"💥 Global crash: {e}")
        send_email("❌ Bdjobs Scraper CRASHED!", f"Scraper crashed with error:\n\n{e}")
