import os
from selenium import webdriver
from dotenv import load_dotenv
from src.main import login_to_linkedin, get_jobs, is_logged_in

load_dotenv(override=True)

LINKEDIN_EMAIL= os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

HOMEPAGE = "https://www.linkedin.com/"
JOBS = "https://www.linkedin.com/jobs/search/?currentJobId=4225329620&f_E=2&keywords=data%20engineer&location=london&origin=JOB_SEARCH_PAGE_JOB_FILTER&originalSubdomain=uk&spellCorrectionEnabled=true"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(r"--user-data-dir=/home/abby/Desktop/My-Personal-Repos/linkedin-job-automation/chrome-profile")
driver = webdriver.Chrome(chrome_options)
# driver.find_element()

if __name__ == "__main__":
    driver.get(HOMEPAGE)
    if not is_logged_in(driver):
        print("❌ Session expired — need to log in again.\n")
        login_to_linkedin(email=LINKEDIN_EMAIL, password=LINKEDIN_PASSWORD, driver=driver)
    else:
        print("✅ Still logged in!\n")
    get_jobs(driver, job_url=JOBS)

    # TODO: Do not forget after everything to close the browser window.