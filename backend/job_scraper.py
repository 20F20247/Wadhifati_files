from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import time
import re
import requests
import logging
import os
import chromedriver_autoinstaller


cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", r"C:\Users\Skmal\Downloads\wadhifati-db-firebase-adminsdk-15rnt-520ef3807a.json")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_driver():
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--ignore-certificate-errors')


    return webdriver.Chrome(options=options)


def get_existing_urls():
    logging.info("Fetching existing job URLs...")
    existing_urls = set()
    docs = db.collection('jobs').stream()
    for doc in docs:
        job = doc.to_dict()
        if 'url' in job:
            existing_urls.add(job['url'])
    logging.info(f"Found {len(existing_urls)} existing URLs.")
    return existing_urls


def scrape_bayt(existing_urls):
    logging.info("Scraping Bayt...")
    base_url = "https://www.bayt.com"
    search_url = "https://www.bayt.com/en/oman/jobs/jobs-in-muscat/"
    response = requests.get(search_url)

    if response.status_code != 200:
        logging.error("Failed to fetch Bayt jobs.")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    job_links = [
        base_url + a_tag['href']
        for a_tag in soup.find_all('a', {'data-js-aid': 'jobID'}, href=True)
        if base_url + a_tag['href'] not in existing_urls
    ]
    logging.info(f"Found {len(job_links)} new Bayt job links.")

    jobs = []
    for job_link in job_links:
        try:
            job_response = requests.get(job_link)
            job_response.raise_for_status()
            job_soup = BeautifulSoup(job_response.content, "html.parser")
            title = job_soup.find('h1', {'id': 'job_title'}).text.strip() if job_soup.find('h1', {'id': 'job_title'}) else "N/A"
            company = job_soup.find('a', class_='t-bold').text.strip() if job_soup.find('a', class_='t-bold') else "Unknown"

            description = "Visit job link for more details."
            description_div = job_soup.find('div', class_='card-content p20t is-spaced')
            if description_div:
                desc_tag = description_div.find('div', class_='t-break')
                if desc_tag:
                    description = desc_tag.get_text(separator=' ').strip()

            jobs.append({
                "title": title,
                "company": company,
                "description": description,
                "source": "Bayt",
                "url": job_link
            })
        except Exception as e:
            logging.error(f"Error scraping Bayt job link {job_link}: {e}")
            continue

    logging.info(f"Scraped {len(jobs)} Bayt jobs.")
    return jobs


def scrape_petrojobs(existing_urls):
    logging.info("Scraping PetroJobs...")
    base_url = "https://www.petrojobs.om"
    search_url = "https://www.petrojobs.om/en-us/Pages/Job/Search_result.aspx?Keyword=&cpn=-1&depid=-1&type=s"

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch PetroJobs: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    job_links = []
    for a_tag in soup.find_all('a', class_='btn btn-primary', href=True):
        match = re.search(r'https://www\.petrojobs\.om/en-us/Pages/Job/Details\.aspx\?i=\d+', a_tag['href'])
        if match:
            full_url = match.group(0)
            if full_url not in existing_urls:
                job_links.append(full_url)

    logging.info(f"Found {len(job_links)} new PetroJobs links.")

    jobs = []
    for job_link in job_links:
        try:
            job_response = requests.get(job_link, timeout=10)
            job_response.raise_for_status()
            job_soup = BeautifulSoup(job_response.content, "html.parser")

            
            title = job_soup.find('span', {'id': 'ctl00_ctl52_g_81bb0e81_7096_42b4_bb00_b771193c1865_lblJobTitle'})
            title = title.text.strip() if title else "N/A"
            company = job_soup.find('span', {'id': 'ctl00_ctl52_g_81bb0e81_7096_42b4_bb00_b771193c1865_lblCompanyName'})
            company = company.text.strip() if company else "Unknown"

            
            description = "Visit job link for more details."
            description_div = job_soup.find('div', {'id': 'ctl00_ctl52_g_81bb0e81_7096_42b4_bb00_b771193c1865_lblJobDescriptionSummary'})
            if description_div:
                description = description_div.get_text(separator=' ').strip()
                logging.info(f"Extracted description: {description}")
            else:
                logging.warning(f"No description found for job link: {job_link}")

            
            jobs.append({
                "title": title,
                "company": company,
                "description": description,
                "source": "PetroJobs",
                "url": job_link
            })
        except Exception as e:
            logging.error(f"Error scraping PetroJobs job link {job_link}: {e}")
            continue

    logging.info(f"Scraped {len(jobs)} PetroJobs jobs.")
    return jobs




def scrape_gulf_talent(driver, existing_urls):
    logging.info("Scraping GulfTalent...")
    try:
        
        driver.get("https://www.gulftalent.com/jobs/search?country=10111116000000")
        time.sleep(15)
        WebDriverWait(driver, 180).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ga-job-impression"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_links = [
            "https://www.gulftalent.com" + a_tag['href']
            for a_tag in soup.find_all('a', class_='ga-job-impression', href=True)
            if "https://www.gulftalent.com" + a_tag['href'] not in existing_urls
        ]
        logging.info(f"Found {len(job_links)} new GulfTalent job links.")

        jobs = []
        for job_link in job_links:
            retry_count = 0
            max_retries = 5
            backoff_time = 5  

            while retry_count < max_retries:
                try:
                   
                    driver.get(job_link)
                    WebDriverWait(driver, 180).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    job_soup = BeautifulSoup(driver.page_source, "html.parser")
                    
                    
                    title = job_soup.select_one('h1.panel-title strong')
                    job_title = title.text.strip() if title else "N/A"
                    company_name_element = job_soup.select_one('a[href^="/companies"]')
                    company_name = company_name_element.text.strip() if company_name_element else "Unknown"
                    job_description_div = job_soup.find('div', class_='panel-body content-visibility-auto')
                    job_description = ' '.join(job_description_div.find('p').stripped_strings) if job_description_div and job_description_div.find('p') else "Visit job link for more details."

                   
                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "description": job_description,
                        "source": "GulfTalent",
                        "url": job_link
                    })
                    break  
                except Exception as e:
                    retry_count += 1
                    logging.warning(f"Retry {retry_count}/{max_retries} for {job_link}: {e}")
                    time.sleep(backoff_time) 
                    backoff_time *= 2
                    if retry_count == max_retries:
                        logging.error(f"Failed to scrape GulfTalent job link {job_link}: {e}")
                        break

                
                time.sleep(5)

        logging.info(f"Scraped {len(jobs)} GulfTalent jobs.")
        return jobs
    except Exception as e:
        logging.error(f"Error in GulfTalent scraper: {e}")
        return []



def store_jobs(jobs):
    logging.info(f"Storing {len(jobs)} jobs...")
    for job in jobs:
        db.collection('jobs').add(job)


def scrape_all_jobs():
    logging.info("Starting job scraping process...")
    driver = get_driver()
    try:
        existing_urls = get_existing_urls()
        bayt_jobs = scrape_bayt(existing_urls)
        store_jobs(bayt_jobs)

        petrojobs = scrape_petrojobs(existing_urls)
        store_jobs(petrojobs)

        gulf_jobs = scrape_gulf_talent(driver, existing_urls)
        store_jobs(gulf_jobs)
    finally:
        driver.quit()
    logging.info("Job scraping process completed.")


if __name__ == "__main__":
    scrape_all_jobs()
