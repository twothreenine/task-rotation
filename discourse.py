from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException # , ElementNotInteractableException
import time

class DiscourseConnector:
    def __init__(self, fsc, url):
        self.driver = fsc.open_driver()
        self.url = url
        self.number_of_tries = 0

    def send_message(self, recipients, subject, body):
        time.sleep(1)
        self.driver.get(f"{self.url}/new-message?username={','.join(recipients)}")
        time.sleep(1)
        try:
            self.driver.find_element(By.ID, "reply-title").send_keys(subject)
        except NoSuchElementException:
            self.number_of_tries += 1
            if self.number_of_tries <= 5: # max tries
                self.send_message(recipients, subject, body)
                return True
            else:
                raise
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//textarea[@class='ember-text-area ember-view d-editor-input']").send_keys(body, Keys.CONTROL, Keys.RETURN)
        time.sleep(1)
        error_popup_button = None
        try:
            error_popup_button = self.driver.find_element(By.XPATH, "//div[@class='dialog-footer']/button")
        except NoSuchElementException:
            return True # success
        print(self.driver.find_element(By.XPATH, "//div[@class='dialog-body']").text)
        error_popup_button.click()
        return False # error, message not sent
