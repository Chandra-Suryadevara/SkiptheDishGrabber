from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import threading
import time
import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class AppiumBackgroundService:
    def __init__(self, appium_server_url='http://localhost:4723'):
        """Initialize the Appium service with configuration."""
        self.appium_server_url = appium_server_url
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Configure and create the Appium driver with proper capabilities."""
        capabilities = {
            'platformName': 'Android',
            'automationName': 'uiautomator2',
            'deviceName': 'Android',
            'appPackage': 'com.delco.courier',
            'appActivity': '.MainActivity',
            'noReset': True,
            'language': 'en',
            'fullReset': False,
            'locale': 'US'
        }

        options = UiAutomator2Options()
        options.load_capabilities(capabilities)
        return webdriver.Remote(self.appium_server_url, options=options)

    def start_service(self):
        """Start the Appium service and initialize the driver."""
        try:
            self.driver = self.setup_driver()
            self.wait = WebDriverWait(self.driver, 60)
            self.logger.info("Driver initialized successfully")

            app_state = self.driver.query_app_state('com.delco.courier')
            if app_state == 3:  # App in background
                self.logger.info("App is in background, terminating...")
                self.driver.terminate_app('com.delco.courier')
            
            self.logger.info("Starting the app...")
            self.driver.activate_app('com.delco.courier')
            return True

        except Exception as e:
            self.logger.error(f"Failed to start service: {str(e)}")
            self.stop_service()
            return False

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present and return it."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {value}")
            return None
        
    def save_page_source(self, filename="page_source.txt"):
        """Save the page source to a text file."""
        try:
            page_source = self.driver.page_source
            with open(filename, "w") as file:
                file.write(page_source)
            self.logger.info(f"Page source saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save page source: {str(e)}")

    def safe_click(self, element):
        """Safely click an element with error handling."""
        try:
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Failed to click element: {str(e)}")
            return False

    def safe_send_keys(self, element, text):
        """Safely send keys to an element with error handling."""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send keys: {str(e)}")
            return False
        
    def select_bottom_bar_option(self, option_index=0):
        """Select an option from the bottom navigation bar."""
        try:
            # Wait for the bottom bar container to appear (you may need to adjust the ID or XPath)
            bottom_bar_container = self.wait_for_element(AppiumBy.ID, 'android:id/navigationBarBackground')
            if not bottom_bar_container:
                raise Exception("Bottom bar container not found")
            
            # Find child elements (assuming they are ImageViews, adjust as necessary)
            option_elements = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.ImageView")  # Or any other appropriate class
            if len(option_elements) <= option_index:
                raise Exception("Selected option index is out of range")

            # Select the option based on the index
            option = option_elements[option_index]
            self.safe_click(option)
            self.logger.info(f"Clicked option {option_index} in the bottom bar")

        except Exception as e:
            self.logger.error(f"Failed to select bottom bar option: {str(e)}")




    def perform_sign_in(self):
        """Handle the sign-in process with proper error handling."""
        try:
            # Wait for initial app load
            time.sleep(30)  # Consider replacing with explicit wait
            
            # Try to sign in
            sign_in_button = self.wait_for_element(AppiumBy.XPATH, '//*[@text="SIGN IN"]')
            if not sign_in_button or not self.safe_click(sign_in_button):
                raise Exception("Could not click initial sign in button")

            # Handle email input
            email_field = self.wait_for_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if not email_field or not self.safe_send_keys(email_field, db.user_name):
                raise Exception("Could not input email")

            # Handle password input
            password_fields = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if len(password_fields) < 2 or not self.safe_send_keys(password_fields[1], db.password):
                raise Exception("Could not input password")

            # Final sign in click
            sign_in_button = self.wait_for_element(AppiumBy.XPATH, '//*[@text="SIGN IN"]')
            if not sign_in_button or not self.safe_click(sign_in_button):
                raise Exception("Could not click final sign in button")

            self.logger.info("Sign in successful")
            time.sleep(5)  # Allow time for sign-in to complete

        except Exception as e:
            self.logger.error(f"Already: {str(e)}")
            try:
                self.find_all_elements_and_save_to_file()
    
                # self.safe_click(scheduling_button)
                # if scheduling_button and self.safe_click(scheduling_button):
                #     time.sleep(5)
                #     open_shifts_button = self.wait_for_element(AppiumBy.XPATH, '//*[@text="Open Shifts"]')
                #     if open_shifts_button:
                #         self.safe_click(open_shifts_button)
                #         time.sleep(60)  # Consider replacing with explicit wait
            except Exception as nested_e:
                self.logger.error(f"Failed to handle alternate flow: {str(nested_e)}")

    def stop_service(self):
        """Safely stop the Appium service."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Service stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping service: {str(e)}")

def start_background_automation():
    """Function to run the automation in a background thread."""
    appium_service = AppiumBackgroundService()
    try:
        if appium_service.start_service():
            appium_service.perform_sign_in()
    finally:
        appium_service.stop_service()

if __name__ == '__main__':
    # Option 1: Run directly
    APP = AppiumBackgroundService()
    try:
        if APP.start_service():
            APP.perform_sign_in()
    finally:
        APP.stop_service()

    # Option 2: Run in background thread
    # background_thread = threading.Thread(target=start_background_automation)
    # background_thread.start()