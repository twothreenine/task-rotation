from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class DiscourseConnector:
    def __init__(self, fsc, url):
        self.driver = fsc.open_driver()
        self.url = url

    def send_message(recipients, subject, body):
        self.driver.get(f"{self.url}/new-message?username={','.join(recipients)}")
        time.sleep(1)
        self.driver.find_element(By.ID, "reply-title").send_keys(subject)
        self.driver.find_element(By.XPATH, "//div[@class='d-editor-textarea-wrapper\n          \n          ']/textarea").send_keys(body)
        self.driver.find_element(By.XPATH, "//button[@class='btn btn-icon-text btn-primary create ']").click()
        time.sleep(1)
