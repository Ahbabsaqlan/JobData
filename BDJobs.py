import pandas as pd
import requests
from bs4 import BeautifulSoup  # for cleaning HTML fields
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import ast
import time

# --- Configuration ---
PAGES_TO_SCRAPE = 55      # Number of listing pages to scrape for job IDs
JOBS_PER_PAGE = 100       # Set to 100 for max jobs per page
API_URL_TEMPLATE = "https://gateway.bdjobs.com/ActtivejobsTest/api/JobSubsystem/jobDetails?jobId={}"

# --- Helper functions ---
def clean_html(raw_html):
    """Strip HTML tags and return plain text."""
    if not raw_html:
        return None
    return BeautifulSoup(raw_html, "html.parser").get_text(separator="\n").strip()

def fetch_job_details_from_api(job_id):
    """Fetch job details JSON from Bdjobs API and return a structured dict."""
    url = API_URL_TEMPLATE.format(job_id)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Failed to fetch job {job_id}, HTTP {resp.status_code}")
            return None
        
        data = resp.json()
        if data.get("statuscode") != "0" or not data.get("data"):
            print(f"⚠️ No valid data for job {job_id}")
            return None
        
        job = data["data"][0]
        
        # Extract and clean relevant fields
        job_data = {
            "Job ID": job.get("JobId"),
            "Job Title": job.get("JobTitle"),
            "Company Name": job.get("CompnayName"),
            "Posted On": job.get("PostedOn"),
            "Deadline": job.get("Deadline"),
            "Vacancies": job.get("JobVacancies"),
            "Job Nature": job.get("JobNature"),
            "Workplace": job.get("JobWorkPlace"),
            "Education Requirements": clean_html(job.get("EducationRequirements")),
            "Experience": clean_html(job.get("experience")),
            "Additional Requirements": clean_html(job.get("AdditionJobRequirements")),
            "Skills Required": job.get("SkillsRequired"),
            "Job Description": clean_html(job.get("JobDescription")),
            "Location": job.get("JobLocation"),
            "Salary Range": job.get("JobSalaryRange"),
            "Company Address": job.get("CompanyAddress"),
            "Apply Email": job.get("ApplyEmail"),
            "Apply Instruction": clean_html(job.get("ApplyInstruction")),
            "Job Link": f"https://jobs.bdjobs.com/jobdetails.asp?id={job_id}"
        }
        return job_data
    
    except Exception as e:
        print(f"❌ Error fetching job {job_id}: {e}")
        return None

# --- Step 1: Collect Job IDs from listing pages ---
options = Options()
# options.add_argument("--headless")  # Uncomment to run in background
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("start-maximized")
driver = webdriver.Chrome(options=options)

job_ids = []

try:
    print(f"--- Starting to collect Job IDs from {PAGES_TO_SCRAPE} pages ---")
    for page_num in range(1, PAGES_TO_SCRAPE + 1):
        try:
            url = f"https://jobs.bdjobs.com/jobsearch.asp?pg={page_num}&rpp={JOBS_PER_PAGE}"
            driver.get(url)
            
            element = driver.find_element("id", "arrTempJobIds")
            
            job_ids_value = element.get_attribute("value")
            ids_on_page = eval(job_ids_value)
            
            job_ids.extend(ids_on_page)
            print(f"✅ Page {page_num}: Found {len(ids_on_page)} job IDs. Total collected: {len(job_ids)}")
            #time.sleep(1)  # Small delay to avoid overwhelming the server
            
        except TimeoutException:
            print(f"⚠️ Warning: Could not find job IDs on page {page_num}. Page might be empty or changed.")
        except Exception as e:
            print(f"❌ Error on page {page_num} while collecting IDs: {e}")

finally:
    print("\n--- Closing WebDriver after ID collection ---")
    driver.quit()

print(f"\n--- Finished collecting IDs. Total Job IDs found: {len(job_ids)} ---")

# --- Step 2: Fetch Job Details from API ---
scraped_data = []

if not job_ids:
    print("No job IDs were collected. Exiting.")
else:
    print(f"\n--- Starting to fetch details for {len(job_ids)} jobs ---")
    for i, job_id in enumerate(job_ids, 1):
        job_details = fetch_job_details_from_api(job_id)
        if job_details:
            scraped_data.append(job_details)
            print(f"✅ Scraped job {i}/{len(job_ids)}: {job_details['Job Title']}")
        #time.sleep(0.5)  # Small delay to avoid hitting API too fast

# --- Step 3: Save to Excel ---
OUTPUT_FILENAME = f"bdjobs_data_refined(July-{len(scraped_data)}).xlsx"
if not scraped_data:
    print("⚠️ No job data was scraped, skipping Excel export.")
else:
    print(f"\n--- Processing {len(scraped_data)} job entries and saving to Excel ---")
    try:
        df = pd.DataFrame(scraped_data)
        
        # Save to Excel
        df.to_excel(OUTPUT_FILENAME, index=False, engine='openpyxl')
        print(f"✅ Success! Data saved to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"❌ Error: Failed to save data to Excel. Reason: {e}")
