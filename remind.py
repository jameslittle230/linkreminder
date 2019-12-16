import os
import time
import random
import requests
import datetime
from database import Database
from datetime import date, timedelta
import xml.etree.ElementTree as ET

MOCK_API_CALLS = False
DEBUG = False

ACCEPTABLE_NOTIF_HOURS = [
    9,
    12,
    16,
    20
]

EXPONENTIAL_STEPS = [
    4,
    8,
    18,
    45,
    90,
    180,
    365
]

db = None


def makeAuthenticatedPinboardRequestOrMock(endpoint, filename):
    if MOCK_API_CALLS:
        with open(filename) as f:
            return f.read()
    else:
        return makeAuthenticatedPinboardRequest(endpoint)


def makeAuthenticatedPinboardRequest(endpoint):
    params = {'auth_token': os.environ['PINBOARD_TOKEN']}
    r = requests.get(f'https://api.pinboard.in/v1/{endpoint}', params=params)
    return r.text


def getAllFromPinboard():
    xml_output = makeAuthenticatedPinboardRequestOrMock(
        'posts/all', 'mock_posts_all_output.xml')
    return ET.fromstring(xml_output)


def normalizeTodaysPosts():
    todays_posts = getPostsForDay(date.today())
    acceptable_post_count = len(ACCEPTABLE_NOTIF_HOURS)
    if len(todays_posts) <= acceptable_post_count:
        return

    # Posts with a lower priority get punted more often. Since priority is based
    # on last update delta, posts at the less frequent end of the exponential
    # backoff get punted less.
    todays_posts.sort(key=lambda x: x["punt_priority"], reversed=True)

    overflow = todays_posts[acceptable_post_count:]
    for post in overflow:
        post["punt_until"] += timedelta(days=1)
        # Decrease the punt priority so there's less of a chance it'll get
        # punted next time
        post["punt_priority"] -= 1
        db.update(post["hash"], post)


def getPostsForDay(date):
    return list(filter(lambda x: x["punt_until"] == date, db.entries()))


def sendSlackMessageForPost(post):
    with open('message.txt') as f:
        template = f.read()
        context = "You've never seen this link before."
        if "last_seen" in post:
            days_since = (date.today() - post["last_seen"]).days
            context = f"You last saw this link {days_since} days ago."
        template = template.replace(
            '<LINK>', post["href"]).replace('<CONTEXT>', context)
        requests.post(os.environ["SLACK_URL"], data=template)
        post["last_seen"] = date.today()
        db.update(post["hash"], post)


def sendCronNotification():
    todays_posts = getPostsForDay(date.today())
    if len(todays_posts) == 0:
        return False

    post = todays_posts[0]
    print(post)
    sendSlackMessageForPost(post)

    next_exponential_step = list(
        filter(lambda x: x > post["next_step"], EXPONENTIAL_STEPS))[0]

    post["punt_until"] += timedelta(days=post["next_step"])
    post["next_step"] = next_exponential_step
    post["punt_priority"] = post["next_step"]

    db.update(post["hash"], post)


def reloadDatabase(rootElement):
    removed = 0
    added = 0
    current_entries = db.entries().copy()

    for child in list(rootElement):
        # If child isn't in database, add it
        matching_entries = list(
            filter(lambda x: x["hash"] == child.attrib["hash"], current_entries))
        if len(matching_entries) == 0:
            punt_date = date.today() + timedelta(days=4)
            addEntryWithPuntDate(child, punt_date)
            added += 1
        # If child is in database, remove it from our temp list
        else:
            current_entries.remove(matching_entries[0])
    # For all database entries without a matching child, delete from database
    for entry in current_entries:
        db.remove(entry["hash"])
        removed += 1

    print(f"Added {added} items and removed {removed} items.")


def cronHandler():
    pinboard_input = getAllFromPinboard()
    hour = datetime.datetime.now().hour
    reloadDatabase(pinboard_input)

    if hour < ACCEPTABLE_NOTIF_HOURS[0]:
        normalizeTodaysPosts()
        return

    if hour in ACCEPTABLE_NOTIF_HOURS or DEBUG == True:
        sendCronNotification()
        return


def addEntryWithPuntDate(xmlElement, date):
    entry = {
        "punt_until": date,
        "next_step": EXPONENTIAL_STEPS[0],
        "punt_priority": EXPONENTIAL_STEPS[0],
        "href": xmlElement.attrib["href"],
        "hash": xmlElement.attrib["hash"]
    }
    db.insert(entry)


def initializeDatabase():
    root = getAllFromPinboard()
    post_list = list(root)
    random.shuffle(post_list)
    number_of_posts = len(post_list)
    today = date.today()
    added = 0
    duplicates = 0

    if len(db.entries()) > 0:
        print(
            f"Database already has {len(db.entries())} entries, cannot reinitialize.")
        return

    for (idx, child) in enumerate(post_list):
        hashes = list(map(lambda x: x["hash"], db.entries()))
        if child.attrib["hash"] in hashes:
            print(f"Duplicate: {child.attrib['href']}")
            duplicates += 1
            continue
        delta = timedelta(days=idx//len(ACCEPTABLE_NOTIF_HOURS))
        punt_until_date = today + delta
        print(punt_until_date)
        addEntryWithPuntDate(child, punt_until_date)
        added += 1
    print(f"Inserted {added} entries. {duplicates} duplicates found.")


if __name__ == "__main__":
    db = Database("db.txt")
    if len(db.entries()) == 0:
        initializeDatabase()
    else:
        cronHandler()
    db.write()
