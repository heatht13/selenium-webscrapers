from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time

class TitleOneScraper():
   
    def __init__(self, service:Service, url:str, username:str, password:str, headless:bool=True):
        self.service= service
        self.options = Options()
        #self.options.add_argument('--headless') if headless else None
        self.driver = WebDriver(service=self.service, options=self.options)
        self.url = url
        self.username = username
        self.password = password

    def connect(self):
        # self.driver.start_client()
        # self.driver.start_session(capabilities={})
        self.driver.get(self.url)
        self.driver.implicitly_wait(3)
    
    def login(self):
        login = self.driver.find_element(By.XPATH, r'//*[@id="root"]/div/nav/div/div/div[2]/button')
        login.click()
        username = self.driver.find_element(By.XPATH, r'//*[@id="UserId"]')
        username.send_keys(self.username)
        password = self.driver.find_element(By.XPATH, r'//*[@id="password"]')
        password.send_keys(self.password)
        submit = self.driver.find_element(By.XPATH, r'//*[@id="next"]')
        submit.click()

    def logout(self):
        self.driver.switch_to.window(self.driver.window_handles[0])
        logout = self.driver.find_element(By.XPATH, r'//*[@id="root"]/div/nav/div/div/div[2]/a[3]')
        logout.click()

    def get_foreclosures(self):
        # next_arrow = self.driver.find_element(By.XPATH, r'//*[@id="root"]/div/div[2]/div[2]/div/button[2]')
        # next_arrow.click()
        wait = WebDriverWait(self.driver, 10)
        foreclosures = str(self.driver.find_elements(By.XPATH, r'//*[@id="root"]/div/div[2]/div[2]/div/div/div/div[18]/div/a')[0].get_attribute("href"))
        self.driver.get(foreclosures)
        link = self.driver.find_element(By.XPATH, r'//*[@id="btnSearch"]')
        original_window = self.driver.current_window_handle
        link.click()
        wait.until(EC.number_of_windows_to_be(2))
        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                break
        counties_dropdown = self.driver.find_element(By.XPATH, r'//*[@id="ctl00_uxMainCPH_uxCountyDdl"]')
        counties = counties_dropdown.find_elements(By.TAG_NAME, "option")
        for county in counties[1:]:
            self.get_foreclosure_data(county)

    def get_foreclosure_data(self, county):
        county.click()
        submit = self.driver.find_element(By.XPATH, r'//*[@id="ctl00_uxMainCPH_uxSubmitBtn"]')
        submit.click()
        time.sleep(2)
        # foreclosure_table = self.driver.find_element(By.XPATH, r'//*[@id="ctl00_uxMainCPH_uxForeclosureGrid"]')
        # foreclosure_rows = foreclosure_table.find_elements(By.TAG_NAME, "tr")
        # for row in foreclosure_rows:
        #     foreclosure_data = row.find_elements(By.TAG_NAME, "td")
        #     for data in foreclosure_data:
        #         print(data.text)
      

if __name__ == '__main__':
    print("Title One Foreclosures\n")
    print("This utility is designed to scrape titleonecorp.com for foreclosures with more than three missed payments.")
    cont = input("Would you like to continue? [y/n]: ")
    if cont not in ('Y', 'y', 'Yes', 'yes', 'YES', 'yES'):
        exit(0)
    #driver_path = input("Please enter the path to your Chrome driver: ")
    driver_path = r"/usr/local/bin/chromedriver"
    service = Service(driver_path)
    url = 'https://www.titleonecorp.com/'
    t1 = TitleOneScraper(service=service, url=url, username='username', password='password', headless=False)
    t1.connect()
    t1.login()
    time.sleep(5)
    t1.get_foreclosures()
    t1.logout()
    time.sleep(5)
