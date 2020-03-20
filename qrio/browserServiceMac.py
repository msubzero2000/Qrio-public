from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import urllib


class BrowserService(object):

    _CHROME_PATH = '/Users/agustinus.nalwan/Downloads/chromedriver'
    _YOUTUBE_KIDS_HOME_URL = "http://youtubekids.com"
    _YOUTUBE_KIDS_SEARCH_URL = "https://www.youtubekids.com/search?q={0}&hl=en-GB"
    _LOAD_TIMEOUT = 5

    def __init__(self, windowPos=(200, 0, 1080, 960)):
        self._setup(windowPos)

    def _setup(self, windowPos):
        self._driver = webdriver.Chrome(BrowserService._CHROME_PATH)
        self._driver.set_window_position(windowPos[0], windowPos[1])
        self._driver.set_window_size(windowPos[2], windowPos[3])

        # Open youtubeKids
        self._driver.get(BrowserService._YOUTUBE_KIDS_HOME_URL)
        self._wait()
        self._driver.find_element_by_id('parent-button').click()
        self._driver.find_element_by_id('next-button').click()
        self._driver.find_element_by_id('onboarding-age-gate-digit-1').send_keys('1')
        self._driver.find_element_by_id('onboarding-age-gate-digit-2').send_keys('9')
        self._driver.find_element_by_id('onboarding-age-gate-digit-3').send_keys('8')
        self._driver.find_element_by_id('onboarding-age-gate-digit-4').send_keys('0')
        self._driver.find_element_by_css_selector(".flow-buttons > #submit-button").click()
        self._driver.find_element_by_id('show-text-link').click()
        self._driver.find_element_by_css_selector('.ytk-kids-flow-text-info-renderer > #next-button').click()
        self._driver.find_element_by_id('skip-button').click()
        time.sleep(2)
        self._driver.find_element_by_css_selector('.ytk-kids-onboarding-parental-notice-page-renderer > #next-button').click()
        time.sleep(2)
        self._driver.find_element_by_xpath("//img[contains(@src,'https://www.gstatic.com/ytkids/onboarding/content_card_broadway/content_level_age_preschool_normal_564_500.png')]").click()
        time.sleep(2)
        self._driver.find_element_by_css_selector('#select-link').click()
        self._driver.find_element_by_css_selector('#search-on-button').click()
        self._driver.find_element_by_css_selector('#done-button').click()

    def _wait(self, elementId='element_id'):
        try:
            element_present = EC.presence_of_element_located((By.ID, elementId))
            WebDriverWait(self._driver, self._LOAD_TIMEOUT).until(element_present)
        except TimeoutException:
            print
            "Timed out waiting for page to load"

    def searchAndPlay(self, keyword):
        keywordEncoded = urllib.parse.quote(keyword, safe='')

        self._driver.get(self._YOUTUBE_KIDS_SEARCH_URL.format(keywordEncoded))
        try:
            self._wait()

            video = self._driver.find_element_by_class_name('yt-simple-endpoint.ytk-compact-video-renderer')
            if video is not None:
                video.click()
                self._wait()
                self._driver.find_element_by_css_selector('#player-fullscreen-button > #icon').click()

                return True
        except Exception as ex:
            pass

        return False

    def stop(self):
        self._driver.find_element_by_css_selector('#player-fullscreen-button > #icon').click()
        self._wait()
        self._driver.get(self._YOUTUBE_KIDS_HOME_URL)

# browser = BrowserService()
# time.sleep(3)
# browser.searchAndPlay("bus")
# time.sleep(10)
# browser.stop()
# time.sleep(1000)

