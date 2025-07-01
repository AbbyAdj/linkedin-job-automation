import logging
import time
from pprint import pprint

from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException, TimeoutException, \
    StaleElementReferenceException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

external_apply = []

def login_to_linkedin(email, password, driver: webdriver.Chrome):
    driver.maximize_window()
    driver.implicitly_wait(3) # no matter how high, immediately the element is ready, code continues execution
    tries = 3
    while True:
        logger.info(f"{tries} login attempts left.")
        print(f"{tries} login attempts left.")
        tries -= 1

        if tries == 0:
            logger.error("Failed to login. Please try again later.")
            print("Failed to login. Please try again later.")
            break

        try:
            sign_in = driver.find_element(By.LINK_TEXT, value="Sign in with email")
            print("Logging you in........")
            sign_in.click()
            time.sleep(2)
            email_input = driver.find_element(By.NAME, value="session_key")
            password_input = driver.find_element(By.NAME, value="session_password")
            email_input.send_keys(email, Keys.TAB)
            password_input.send_keys(password, Keys.ENTER)
            if "feed" in driver.current_url:
                print("Login Successful\n\n")
                logger.info("Login Successful")
                break
            else:
                raise Exception("Login did not succeed. Possibly a security check.")

        except Exception as e:
            print(e)

def is_logged_in(driver) -> bool:
    try:
        # Wait a few seconds for the page to load
        WebDriverWait(driver, 10).until(lambda d: d.current_url is not None)
        return "feed" in driver.current_url
    except TimeoutException:
        return False

def security_check(email, password, driver: webdriver.Chrome):
    # TODO: Need to reimplement, involves images.
    print("Suspicious activity noticed....\n Rectifying it......")
    sign_in = driver.find_element(By.LINK_TEXT, "Sign in")
    sign_in.click()
    email_input = driver.find_element(By.NAME, value="session_key")
    password_input = driver.find_element(By.NAME, value="session_password")
    email_input.send_keys(email, Keys.TAB)
    password_input.send_keys(password, Keys.ENTER)
    print("Login Successful\n\n")
    logger.info("Login Successful")

def load_jobs_on_page(driver, jobs_list_li_xpath)->list:
    count = 0
    jobs_list = []

    print("Loading jobs on this page.....   ")
    for _ in range(10):
        jobs_list = driver.find_elements(By.XPATH, jobs_list_li_xpath)
        if not jobs_list:
            break

        last_job = jobs_list[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", last_job)
        time.sleep(2.5)

        jobs_list = driver.find_elements(By.XPATH, jobs_list_li_xpath)
        curr_count = len(jobs_list)

        if curr_count == count:
            print("No new jobs loaded — stopping scroll.")
            break

        count = curr_count

    print(f"{count} jobs loaded.")
    return jobs_list

def get_company_name(driver)-> str:
    ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    company_name_xpath = '''//*[@id="main"]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]
                            /div/div[1]/div/div[1]/div/div[1]/div[1]/div/a'''

    company_name = (WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions)
                    .until(expected_conditions.presence_of_element_located((By.XPATH, company_name_xpath
                                                                            ))))
    try:
        company_name_text = company_name.text
        return company_name_text
    except StaleElementReferenceException:
        time.sleep(0.5)
        company_name = driver.find_element(By.XPATH, company_name_xpath)
        company_name_text = company_name.text
        return company_name_text

def get_jobs(driver: webdriver, job_url):
    driver.get(job_url)
    driver.minimize_window()
    driver.implicitly_wait(3)  # no matter how high, immediately the element is ready, code continues execution

    jobs_list_li_xpath = '//*[@id="main"]/div/div[2]/div[1]/div/ul/li[.//a]'
    jobs_list = load_jobs_on_page(driver, jobs_list_li_xpath)

    tracker = {
        "Applied": 0,
        "Saved": 0,
        "Skipped": 0,
    }
    applied_applications = {}
    saved_applications = {}
    skipped_applications = {}

    for i, job in enumerate(jobs_list):
        job_title = company_name = ""
        try:
            time.sleep(0.5)
            job.click()
            job_title = job.find_elements(By.XPATH, ".//a")
            job_title_text = job_title[0].text.split("\n")[0]
            print(f"{'-' * 40}\nJob {i + 1}:\n{job_title_text}\n")

            company_name_text = get_company_name(driver)
            print(f"Company {i + 1}:\n{company_name_text}\n")

            try:
                easy_apply_button = driver.find_element(
                    By.XPATH, '//*[@id="jobs-apply-button-id"]'
                )
                easy_apply_button_text = easy_apply_button.text

            except NoSuchElementException:
                # We can assume that by easy apply not being found, the job has already been applied to

                print(
                    f"{job_title_text} at {company_name_text} has already been applied to. Skipping"
                )
                tracker["Skipped"] += 1
                skipped_applications[tracker["Skipped"]] = {
                    "job_title": job_title_text,
                    "company_name": company_name_text,
                }

            else:
                if "Easy Apply" in easy_apply_button_text:
                    print(f"Applying to {job_title_text} at {company_name_text}\n")
                    applied = easy_apply(driver, easy_apply_button=easy_apply_button)
                    if applied:
                        tracker["Applied"] += 1
                        applied_applications[tracker["Applied"]] = {
                            "job_title": job_title_text,
                            "company_name": company_name_text,
                        }
                    else:
                        tracker["Skipped"] += 1
                        skipped_applications[tracker["Skipped"]] = {
                            "job_title": job_title_text,
                            "company_name": company_name_text,
                        }

                elif "Apply" in easy_apply_button_text:
                    print(f"Saving {job_title_text} at {company_name_text}\n")
                    tracker["Saved"] += 1
                    job_url = collect_job_url(
                        driver, easy_apply_button=easy_apply_button
                    )
                    print(f"job_url:{job_url}")
                    saved_applications[tracker["Saved"]] = {
                        "job_title": job_title_text,
                        "company_name": company_name_text,
                        "apply_link": job_url,
                    }
                else:
                    print("Can't be applied to by easy apply or apply")

        except Exception as e:
            print(
                f"Job {i + 1}: Error occurred during process for {job_title} at {company_name} – {e}\n{'-' * 40}"
            )

    # print(f"{'-' * 40}\n{tracker}\n{'-' * 40}")
    # pprint({applied_applications}) if applied_applications else ""
    # pprint(saved_applications) if saved_applications else ""
    # pprint(skipped_applications) if skipped_applications else ""

    all_trackers = {
        "tracker": tracker,
        "applied": applied_applications,
        "saved": saved_applications,
        "skipped": skipped_applications,
    }
    return all_trackers

def easy_apply(driver, easy_apply_button)-> bool:
    # To check if the job has already been applied to:
    try:
        easy_apply_button.click()

        submit_application = driver.find_element(By.XPATH, '//button[starts-with(@id, "ember") and contains(text(), "Submit")]')
        submit_application.click()

        print("Job application complete!")

    except NoSuchElementException as e:
        print("Complex application process. Skipping....")
        dismiss_popup = driver.find_element(By.XPATH, '//button[@aria-label="Dismiss"]')
        dismiss_popup.click()
        # complex_easy_apply(driver)

        time.sleep(0.5)

        discard = driver.find_element(By.XPATH, '//button[.//span[text()="Discard"]]')
        discard.click()
        return False

    except Exception as e:
        print(f"An unknown error occurred during easy apply - {e}")
        return False

    else:
        dismiss_popup = driver.find_element(By.XPATH, '//button[@aria-label="Dismiss"]')
        dismiss_popup.click()
        return True

def complex_easy_apply(driver):
    pass

def collect_job_url(driver, easy_apply_button)-> str | None:
    try:
        wait = WebDriverWait(driver, 10)
        original_window = driver.current_window_handle
        easy_apply_button.click()
        wait.until(expected_conditions.number_of_windows_to_be(2))
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        external_apply_url = driver.current_url
        driver.close()
        driver.switch_to.window(original_window)
        return external_apply_url

    except Exception as e:
        print(f"An unknown error occurred during easy apply - {e}")
        return None

def send_data(saved_jobs: dict):
    pass

