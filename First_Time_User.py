from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Tuple
import threading
import time
import db
import json

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
        
    def find_bottom_navigation_buttons(self):
        """Find and log all clickable elements at the bottom of the screen."""
        try:
            found_buttons = []
            try:
                screen_size = self.driver.get_window_size()
                screen_height = screen_size['height']
                bottom_area_start = int(screen_height * 0.8)
                bottom_elements = self.driver.find_elements(AppiumBy.XPATH, 
                    f'//android.widget.Button | //android.view.View[@clickable="true"] | //android.widget.TextView[@clickable="true"]')
                for element in bottom_elements:
                    try:
                        location = element.location
                        if location['y'] > bottom_area_start:
                            text = element.get_attribute('text') or element.get_attribute('content-desc')
                            if text and (text, element) not in found_buttons:
                                found_buttons.append(element)
                    except Exception as e:
                        continue
            except Exception as e:
                self.logger.error(f"Error finding bottom elements: {str(e)}")
            if found_buttons:
                return found_buttons
            else:
                self.logger.warning("No navigation buttons found")
                return []
        except Exception as e:
            self.logger.error(f"Error in finding navigation buttons: {str(e)}")
            return []
    
    def find_navigation_buttons(self, position='bottom'):
        """Find and log all clickable elements at the specified position of the screen.
        
        Args:
            position (str): Position to search for navigation buttons. 
                        Accepted values: 'top' or 'bottom'. Defaults to 'bottom'.
        
        Returns:
            list: List of WebElement objects representing clickable elements in the specified navigation area
        
        Raises:
            ValueError: If position parameter is neither 'top' nor 'bottom'
        """
        try:
            # Validate position parameter
            if position.lower() not in ['top', 'bottom']:
                raise ValueError("Position must be either 'top' or 'bottom'")
                
            found_buttons = []
            try:
                screen_size = self.driver.get_window_size()
                screen_height = screen_size['height']
                
                # Calculate threshold based on position
                if position.lower() == 'bottom':
                    threshold = int(screen_height * 0.8)  # Start of bottom 20%
                    position_check = lambda y: y > threshold
                else:  # top
                    threshold = int(screen_height * 0.2)  # End of top 20%
                    position_check = lambda y: y < threshold
                
                # Find all potentially clickable elements
                elements = self.driver.find_elements(AppiumBy.XPATH,
                    '//android.widget.Button | //android.view.View[@clickable="true"] | //android.widget.TextView[@clickable="true"]')
                
                for element in elements:
                    try:
                        location = element.location
                        # Check if element is in the target area using the appropriate position check
                        if position_check(location['y']):
                            text = element.get_attribute('text') or element.get_attribute('content-desc')
                            if text and element not in found_buttons:
                                found_buttons.append(element)
                    except Exception as e:
                        self.logger.debug(f"Failed to process element: {str(e)}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error finding {position} elements: {str(e)}")
                
            if found_buttons:
                self.logger.info(f"Found {len(found_buttons)} navigation buttons in {position} area")
                return found_buttons
            else:
                self.logger.warning(f"No {position} navigation buttons found")
                return []
                
        except Exception as e:
            self.logger.error(f"Error in finding {position} navigation buttons: {str(e)}")
            return []
        
        
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
                self.logger.info("Looking for navigation buttons...")
                bottom_nav_buttons = self.find_navigation_buttons('bottom')
                Scheduling = bottom_nav_buttons[1]
                self.safe_click(Scheduling)
                time.sleep(5)
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
     #Option 1: Run directly
     APP = AppiumBackgroundService()
     try:
         if APP.start_service():
             APP.perform_sign_in()
     finally:
         APP.stop_service()

    # Option 2: Run in background thread
    # background_thread = threading.Thread(target=start_background_automation)  
    # background_thread.start()