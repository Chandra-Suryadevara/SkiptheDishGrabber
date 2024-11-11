def find_and_click_scheduling(self):
        """
        Find and click the Scheduling button using various strategies.
        Returns True if successful, False otherwise.
        """
        try:
            # Try different strategies to find clickable elements near the navigation bar area
            
            # Strategy 1: Find all clickable elements in the bottom area using bounds
            bottom_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//*[@clickable='true' and contains(@bounds, '3036')]"
            )
            
            if not bottom_elements:
                # Strategy 2: Find all ImageView elements in the bottom area
                bottom_elements = self.driver.find_elements(
                    AppiumBy.XPATH,
                    "//android.widget.ImageView[contains(@bounds, '3036')]"
                )
                
            if not bottom_elements:
                # Strategy 3: Get all elements in the bottom area
                bottom_elements = self.driver.find_elements(
                    AppiumBy.XPATH,
                    "//*[contains(@bounds, '3036')]"
                )

            # Log what we found
            self.logger.info(f"Found {len(bottom_elements)} elements in the bottom area")
            
            scheduling_button = None
            for idx, element in enumerate(bottom_elements):
                try:
                    content_desc = element.get_attribute("content-desc")
                    resource_id = element.get_attribute("resource-id")
                    text = element.get_attribute("text")
                    class_name = element.get_attribute("className")
                    bounds = element.get_attribute("bounds")
                    clickable = element.get_attribute("clickable")
                    
                    self.logger.info(f"""
                    Element {idx + 1}:
                    - Class: {class_name}
                    - Content Description: {content_desc}
                    - Resource ID: {resource_id}
                    - Text: {text}
                    - Bounds: {bounds}
                    - Clickable: {clickable}
                    """)
                    
                    # Check if this might be the scheduling button
                    if (content_desc and "schedule" in content_desc.lower()) or \
                    (resource_id and "schedule" in resource_id.lower()) or \
                    (text and "schedule" in text.lower()):
                        scheduling_button = element
                        self.logger.info("Found potential scheduling button through attributes")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error checking element {idx + 1}: {str(e)}")
                    continue

            # If we still haven't found it, try clicking the third element (if it exists)
            if not scheduling_button and len(bottom_elements) >= 3:
                scheduling_button = bottom_elements[2]  # Adjust index if needed
                self.logger.info("Using index-based selection for scheduling button")

            if scheduling_button:
                # Try to make the element clickable if it's not
                self.driver.execute_script('mobile: clickGesture', {
                    'x': int(scheduling_button.rect['x'] + scheduling_button.rect['width']/2),
                    'y': int(scheduling_button.rect['y'] + scheduling_button.rect['height']/2)
                })
                
                self.logger.info("Performed click gesture on scheduling button")
                time.sleep(5)  # Wait for navigation
                
                # Verify the navigation worked
                open_shifts_elements = self.driver.find_elements(
                    AppiumBy.XPATH,
                    "//*[contains(@text, 'Open') or contains(@content-desc, 'Open')]"
                )
                
                if open_shifts_elements:
                    self.logger.info("Successfully navigated to Scheduling section")
                    return True
                else:
                    self.logger.warning("Could not verify navigation to Scheduling section")
                    return False
            else:
                self.logger.error("Could not find scheduling button in bottom area")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in find_and_click_scheduling: {str(e)}")
            return False
    def find_all_elements_and_save_to_file(self, filename="all_elements.txt"):
        """
        Find all elements on the current screen and save their details to a file.
        
        Args:
            filename (str): Name of the file to save the elements information to. Defaults to "all_elements.txt"
        """
        try:
            # Get all elements on the screen
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*")
            
            # Open file to write
            with open(filename, "w", encoding='utf-8') as file:
                file.write(f"Total elements found: {len(elements)}\n\n")
                
                # Process each element
                for idx, element in enumerate(elements, 1):
                    try:
                        # Get all possible attributes
                        element_info = {
                            'index': element.get_attribute('index'),
                            'package': element.get_attribute('package'),
                            'class': element.get_attribute('className'),
                            'text': element.get_attribute('text'),
                            'resource-id': element.get_attribute('resource-id'),
                            'checkable': element.get_attribute('checkable'),
                            'checked': element.get_attribute('checked'),
                            'clickable': element.get_attribute('clickable'),
                            'enabled': element.get_attribute('enabled'),
                            'focusable': element.get_attribute('focusable'),
                            'focused': element.get_attribute('focused'),
                            'long-clickable': element.get_attribute('long-clickable'),
                            'password': element.get_attribute('password'),
                            'scrollable': element.get_attribute('scrollable'),
                            'selected': element.get_attribute('selected'),
                            'bounds': element.get_attribute('bounds'),
                            'displayed': element.get_attribute('displayed'),
                            'content-desc': element.get_attribute('content-desc')
                        }
                        
                        # Format the element information
                        element_str = (
                            f"Element {idx}:\n"
                            f"<{element_info['class']} "
                            f"index=\"{element_info['index']}\" "
                            f"package=\"{element_info['package']}\" "
                            f"class=\"{element_info['class']}\" "
                            f"text=\"{element_info['text']}\" "
                            f"resource-id=\"{element_info['resource-id']}\" "
                            f"checkable=\"{element_info['checkable']}\" "
                            f"checked=\"{element_info['checked']}\" "
                            f"clickable=\"{element_info['clickable']}\" "
                            f"enabled=\"{element_info['enabled']}\" "
                            f"focusable=\"{element_info['focusable']}\" "
                            f"focused=\"{element_info['focused']}\" "
                            f"long-clickable=\"{element_info['long-clickable']}\" "
                            f"password=\"{element_info['password']}\" "
                            f"scrollable=\"{element_info['scrollable']}\" "
                            f"selected=\"{element_info['selected']}\" "
                            f"bounds=\"{element_info['bounds']}\" "
                            f"displayed=\"{element_info['displayed']}\" "
                        )
                        
                        # Add content-desc if it exists
                        if element_info['content-desc']:
                            element_str += f"content-desc=\"{element_info['content-desc']}\" "
                        
                        element_str += "/>\n\n"
                        
                        # Write to file
                        file.write(element_str)
                        
                        # Log to console as well
                        self.logger.info(f"Processed element {idx}")
                        
                        # Specifically log if element is in bottom navigation area
                        if element_info['bounds'] and '3036' in str(element_info['bounds']):
                            self.logger.info(f"Found element in bottom navigation area: {element_str}")
                    
                    except Exception as elem_e:
                        self.logger.error(f"Error processing element {idx}: {str(elem_e)}")
                        continue
                
                # Write summary at the end
                file.write("\nSummary:\n")
                file.write(f"Total elements processed: {len(elements)}\n")
                
            self.logger.info(f"Successfully saved all elements to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to find or save elements: {str(e)}")
            return False
        
    def debug_nav_area(self):
        """
        Helper function to debug all elements in the navigation area
        """
        try:
            # Get all elements in the bottom area of the screen
            elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//*[contains(@bounds, '3036')]"
            )
            
            self.logger.info(f"Found {len(elements)} elements in bottom area")
            
            for idx, element in enumerate(elements):
                try:
                    self.logger.info(f"""
                    Element {idx + 1}:
                    - Class: {element.get_attribute('className')}
                    - Resource ID: {element.get_attribute('resource-id')}
                    - Content Desc: {element.get_attribute('content-desc')}
                    - Text: {element.get_attribute('text')}
                    - Bounds: {element.get_attribute('bounds')}
                    - Clickable: {element.get_attribute('clickable')}
                    - Enabled: {element.get_attribute('enabled')}
                    """)
                except Exception as e:
                    self.logger.error(f"Error getting element {idx + 1} details: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error in debug_nav_area: {str(e)}")

def get_element_details(self, element):
        """Get all details about an element in a dictionary format."""
        details = {}  # Empty dictionary to store element details
        
        try:
            # Basic attributes
            details = {
                'text': element.get_attribute('text'),
                'content_desc': element.get_attribute('content-desc'),
                'resource_id': element.get_attribute('resource-id'),
                'class_name': element.get_attribute('className'),
                'bounds': element.get_attribute('bounds'),
                'location': {
                    'x': element.location['x'],
                    'y': element.location['y']
                },
                'size': {
                    'width': element.size['width'],
                    'height': element.size['height']
                }
            }
            
            # Print the details for debugging
            self.logger.info("Button details:")
            for key, value in details.items():
                self.logger.info(f"{key}: {value}")
                
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting element details: {str(e)}")
            return details


