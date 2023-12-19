from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from collections import deque
import logging
from threading import Thread

selectors = {
    "Container": "[data-testid='primaryColumn']",
    "Bio": "[data-testid='UserDescription']",
    "FollowingFollowers": ".css-175oi2r:not(.r-1mf7evn) .r-bcqeeo.r-qvutc0.r-poiln3.r-1b43r93.r-1cwl3u0.r-b88u0q span",
    "Location": "[data-testid='UserLocation']",
    "Website": "[data-testid='UserUrl']",
}

driver: webdriver.Firefox


class TwitterUser:
    bio: str
    following: int
    followers: int
    location: str
    website: str

    def __init__(self, bio, following, followers, location, website):
        self.bio = bio
        self.following = following
        self.followers = followers
        self.location = location
        self.website = website


""" 
Flow of operations:
1. Initialise the webdriver             with `start_scraping_twitter`.
2. Scrape raw data from the given links with `scrape_raw_twitter_data`
4. Free driver
3. Get needed information from data     with `structure_twitter_data`  (threaded)
5. Stop
"""


def scrape_twitter(links: [str], log: bool = True) -> [TwitterUser]:
    information = deque()
    data: [TwitterUser] = []

    saved_logging_level = logging.getLogger().getEffectiveLevel()

    if log:
        logging.getLogger().setLevel(logging.INFO)

    # 1. Initialise the webdriver
    logging.info("Initialising driver.")
    start_scraping_twitter()
    # 2. Scrape raw data from the given links
    logging.info("Scraping data. This may take long.")
    scrape_raw_twitter_data(links, information)
    logging.info("Scraping done. Quitting driver.")
    # 3. Free driver
    driver.quit()
    logging.info("Extracting useful information.")
    # 4. Scrape needed information from data (threaded)
    for _ in range(4):
        Thread(target=structure_twitter_data, args=(information, data)).start()

    # only continute once the threads are done
    while len(information) != 0:
        pass

    logging.info("All done.")

    logging.getLogger().setLevel(saved_logging_level)

    return data


def start_scraping_twitter():
    global driver

    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)


def scrape_raw_twitter_data(links: [str], information: deque):
    global driver

    for link in links:
        driver.get(link)
        # essential exception handling since we don't want to stop at any point
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selectors["FollowingFollowers"])
                )
            )
        except:
            logging.exception(f"Exception with link {link}")
            continue

        container = driver.find_element(
            By.CSS_SELECTOR, selectors["Container"]
        ).get_attribute("innerHTML")
        information.append(container)


def structure_twitter_data(information: deque, data: [TwitterUser]):
    # this is why deques are superior to generic queues!
    while len(information) != 0:
        i = information.popleft()

        soup = BeautifulSoup(i, "html.parser")
        bio = soup.select_one(selectors["Bio"])

        following_followers = soup.select(selectors["FollowingFollowers"])
        following = following_followers[0]
        followers = following_followers[1]

        location = soup.select_one(selectors["Location"])
        website = soup.select_one(selectors["Website"])

        user = TwitterUser(
            bio.text if bio else None,
            following.text,
            followers.text,
            location.text if location else None,
            website.text if website else None,
        )

        data.append(user)
