import time
import random
import string
import os
import shutil
import tempfile
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading


class YouTubeMultiPlayer:
    def __init__(self):
        self.drivers = []
        self.threads = []
        self.active_instances = 0
        self.lock = threading.Lock()
        self.profile_dirs = []  # Keep track of profile directories for cleanup

    def generate_random_user_agent(self):
        """Generate a random user agent string"""
        chrome_versions = ['91.0.4472.124', '92.0.4515.107', '93.0.4577.63', '94.0.4606.61', '95.0.4638.54']
        os_list = [
            'Windows NT 10.0; Win64; x64',
            'Windows NT 6.1; Win64; x64',
            'Macintosh; Intel Mac OS X 10_15_7',
            'X11; Linux x86_64'
        ]

        chrome_version = random.choice(chrome_versions)
        os_string = random.choice(os_list)

        return f'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36'

    def generate_random_profile_name(self):
        """Generate a truly unique profile name using UUID and timestamp"""
        timestamp = str(int(time.time() * 1000))  # Current time in milliseconds
        unique_id = str(uuid.uuid4())[:8]  # Short UUID
        return f"profile_{timestamp}_{unique_id}"

    def create_browser_instance(self, instance_id, youtube_url):
        """Create a browser instance with unique fingerprint"""
        driver = None
        profile_dir = None
        try:
            chrome_options = Options()

            # Create unique profile directory using temp directory
            profile_name = self.generate_random_profile_name()
            temp_dir = tempfile.gettempdir()
            profile_dir = os.path.join(temp_dir, "chrome_profiles", profile_name)

            # Ensure the profile directory doesn't exist (clean slate)
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir, ignore_errors=True)

            # Create the directory
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={profile_dir}')

            # Keep track of profile directory for cleanup
            with self.lock:
                self.profile_dirs.append(profile_dir)

            # Add random user agent
            user_agent = self.generate_random_user_agent()
            chrome_options.add_argument(f'--user-agent={user_agent}')

            # Additional options to make each instance unique and improve stability
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-extensions-file-access-check')
            chrome_options.add_argument('--disable-extensions-http-throttling')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-sync')

            # Disable notifications and popups
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')

            # Add unique remote debugging port
            debug_port = 9222 + instance_id
            chrome_options.add_argument(f'--remote-debugging-port={debug_port}')

            # Random window size
            width = random.randint(800, 1200)
            height = random.randint(600, 900)
            chrome_options.add_argument(f'--window-size={width},{height}')

            # Random window position
            x_pos = random.randint(0, 300)
            y_pos = random.randint(0, 200)
            chrome_options.add_argument(f'--window-position={x_pos},{y_pos}')

            print(f"Instance {instance_id}: Starting browser with profile: {profile_name}")

            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)

            # Successfully created, add to tracking
            with self.lock:
                self.drivers.append(driver)
                self.active_instances += 1

            print(f"Instance {instance_id}: ✅ Browser started successfully")

            # Navigate to YouTube video
            driver.get(youtube_url)
            print(f"Instance {instance_id}: Navigated to YouTube URL")

            # Wait longer for YouTube to fully load
            print(f"Instance {instance_id}: Waiting for page to load...")
            time.sleep(5)  # Give YouTube time to initialize

            # Wait for the video player to be present
            try:
                video_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'video'))
                )
                print(f"Instance {instance_id}: Video player found")

                # Wait a bit more for the player to be ready
                time.sleep(3)

                # Try multiple methods to start the video
                video_started = False

                # Method 1: Click the large play button if it exists
                try:
                    large_play_button = driver.find_element(By.CSS_SELECTOR, '.ytp-large-play-button')
                    if large_play_button.is_displayed():
                        large_play_button.click()
                        print(f"Instance {instance_id}: Clicked large play button")
                        video_started = True
                except NoSuchElementException:
                    pass

                # Method 2: If no large play button, try clicking the video itself
                if not video_started:
                    try:
                        video_element.click()
                        print(f"Instance {instance_id}: Clicked video element")
                        video_started = True
                    except Exception as e:
                        print(f"Instance {instance_id}: Could not click video: {e}")

                # Method 3: Try the regular play button
                if not video_started:
                    try:
                        play_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
                        play_button.click()
                        print(f"Instance {instance_id}: Clicked play button")
                        video_started = True
                    except NoSuchElementException:
                        pass

                # Check if video is actually playing
                time.sleep(2)
                try:
                    is_paused = driver.execute_script("return document.querySelector('video').paused;")
                    if not is_paused:
                        print(f"Instance {instance_id}: ✅ Video is playing successfully!")
                    else:
                        print(f"Instance {instance_id}: ⚠️ Video appears to be paused")
                        # Try one more time to start it
                        driver.execute_script("document.querySelector('video').play();")
                        time.sleep(1)
                        is_paused = driver.execute_script("return document.querySelector('video').paused;")
                        if not is_paused:
                            print(f"Instance {instance_id}: ✅ Video started via JavaScript!")
                except Exception as e:
                    print(f"Instance {instance_id}: Could not check video status: {e}")

            except TimeoutException:
                print(f"Instance {instance_id}: ❌ Failed to load video player within timeout")
                return

            print(f"Instance {instance_id}: Browser session is active and ready")

            # Keep the browser alive until interrupted
            try:
                while True:
                    time.sleep(10)
                    # Check if browser is still alive
                    try:
                        driver.current_url
                    except:
                        print(f"Instance {instance_id}: Browser session ended")
                        break
            except:
                pass

        except Exception as e:
            print(f"Instance {instance_id}: ❌ Error creating browser instance: {str(e)}")
        finally:
            # Clean up this instance
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                with self.lock:
                    if driver in self.drivers:
                        self.drivers.remove(driver)
                    self.active_instances -= 1

            # Clean up profile directory
            if profile_dir and os.path.exists(profile_dir):
                try:
                    shutil.rmtree(profile_dir, ignore_errors=True)
                    print(f"Instance {instance_id}: Cleaned up profile directory")
                except:
                    pass

            print(f"Instance {instance_id}: Cleaned up")

    def open_multiple_instances(self, youtube_url, num_instances):
        """Open multiple YouTube instances"""
        print(f"Opening {num_instances} YouTube instances...")
        print(f"URL: {youtube_url}")
        print("-" * 50)

        # Create threads for each instance
        for i in range(num_instances):
            thread = threading.Thread(
                target=self.create_browser_instance,
                args=(i + 1, youtube_url)
            )
            # Don't use daemon threads so we can properly track when they finish
            thread.daemon = False
            self.threads.append(thread)
            thread.start()

            # Delay between starting instances to avoid overwhelming the system
            time.sleep(3)

        # Wait for all instances to be created (but not necessarily finished)
        time.sleep(5)

        with self.lock:
            current_active = self.active_instances

        print(f"\n✅ Successfully started {current_active} out of {num_instances} instances!")

        if current_active > 0:
            print("All instances are running. Press Ctrl+C to close all instances")
            print("-" * 50)

            try:
                # Keep the main thread alive and monitor instances
                while True:
                    with self.lock:
                        active_count = self.active_instances

                    if active_count == 0:
                        print("All instances have been closed.")
                        break

                    time.sleep(2)

            except KeyboardInterrupt:
                print("\n\nInterrupt received. Closing all instances...")
                self.cleanup()
        else:
            print("No instances were successfully started.")

    def cleanup(self):
        """Clean up all browser instances"""
        print("Closing all browser instances...")
        drivers_copy = self.drivers.copy()  # Create a copy to avoid modification during iteration

        for i, driver in enumerate(drivers_copy):
            try:
                driver.quit()
                print(f"✅ Closed instance {i + 1}")
            except Exception as e:
                print(f"⚠️ Error closing instance {i + 1}: {str(e)}")

        self.drivers.clear()
        with self.lock:
            self.active_instances = 0

        # Clean up profile directories
        print("Cleaning up profile directories...")
        for profile_dir in self.profile_dirs:
            try:
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir, ignore_errors=True)
            except:
                pass
        self.profile_dirs.clear()

        print("All instances have been closed.")


def main():
    # Get YouTube URL from user
    youtube_url = input("Enter YouTube video URL: ").strip()

    # Validate URL
    if not youtube_url.startswith('https://www.youtube.com/watch') and not youtube_url.startswith('https://youtu.be/'):
        print("❌ Please enter a valid YouTube URL")
        return

    # Get number of instances
    try:
        num_instances = int(input("Enter number of instances to open (1-10): "))
        if num_instances <= 0 or num_instances > 10:
            print("❌ Please enter a number between 1 and 10")
            return
    except ValueError:
        print("❌ Please enter a valid number")
        return

    print("\n" + "=" * 50)
    print("STARTING YOUTUBE MULTI-INSTANCE PLAYER")
    print("=" * 50)

    # Create and run the multi-player
    player = YouTubeMultiPlayer()
    player.open_multiple_instances(youtube_url, num_instances)


if __name__ == "__main__":
    print("🎬 YouTube Multi-Instance Player")
    print("=" * 50)
    print("This program will open multiple YouTube video instances")
    print("with different browser profiles and user agents.")
    print("Each instance will attempt to auto-play the video.")
    print("")

    main()