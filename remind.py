import os
# import ssl
import time
import random
import logging
import requests
import datetime
import argparse
import s3uploader
import databaseToHtml
from database import Database
from datetime import date, timedelta
import xml.etree.ElementTree as ET

MOCK_API_CALLS = True
DEBUG_METHODS = True

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

l = logging.getLogger()
logging.basicConfig(level=logging.INFO)


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


def normalizePosts():
    outdated = 0
    for entry in getPostsBeforeDay(date.today()):
        entry["punt_until"] = date.today() + timedelta(days=3)
        db.update(entry["hash"], entry)
        outdated += 1
    l.info(f"Updated {outdated} outdated posts.")

    todays_posts = getPostsForDay(date.today())
    acceptable_post_count = len(ACCEPTABLE_NOTIF_HOURS)
    if len(todays_posts) <= acceptable_post_count:
        return

    l.info(f"{len(todays_posts)} posts scheduled for today; normalizing to {len(ACCEPTABLE_NOTIF_HOURS)}.")

    # Posts with a lower priority get punted more often. Since priority is based
    # on last update delta, posts at the less frequent end of the exponential
    # backoff get punted less.
    todays_posts.sort(key=lambda x: x["punt_priority"], reverse=True)

    overflow = todays_posts[acceptable_post_count:]
    for post in overflow:
        post["punt_until"] += timedelta(days=1)
        # Decrease the punt priority so there's less of a chance it'll get
        # punted next time
        post["punt_priority"] -= 1
        db.update(post["hash"], post)


def getPostsForDay(date):
    return list(filter(lambda x: x["punt_until"] == date, db.entries()))


def getPostsBeforeDay(date):
    return list(filter(lambda x: x["punt_until"] < date, db.entries()))


def sendSlackMessageForPost(post):
    filedir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(filedir, 'message.txt')) as f:
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
    l.debug(todays_posts)
    if len(todays_posts) == 0:
        l.info("No posts remaining today, no message sent.")
        return False

    post = todays_posts[0]
    l.info(post)
    sendSlackMessageForPost(post)

    next_exponential_step = list(
        filter(lambda x: x > post["next_step"], EXPONENTIAL_STEPS))[0]

    post["punt_until"] += timedelta(days=post["next_step"])
    post["next_step"] = next_exponential_step
    post["punt_priority"] = post["next_step"]

    db.update(post["hash"], post)


def reloadDatabase():
    post_list = list(getAllFromPinboard())
    current_entries = db.entries().copy()
    number_of_posts = len(post_list)
    added = 0
    deleted = 0
    duplicates = 0

    for child in post_list:
        hashes_in_db = list(map(lambda x: x["hash"], current_entries))
        if child.attrib["hash"] in hashes_in_db:
            duplicates += 1
            continue
        punt_until_date = date.today() + timedelta(4)
        addEntryWithPuntDate(child, punt_until_date)
        added += 1

    current_entries = db.entries().copy()

    hashes_from_server = list(map(lambda x: x.attrib["hash"], post_list))
    for entry in current_entries:
        if entry["hash"] in hashes_from_server:
            continue
        # otherwise, entry is in database, but isn't on the server
        db.remove(entry["hash"])
        deleted += 1

    l.info(
        f"Inserted {added} entries and deleted {deleted} entries. {duplicates} duplicates found.")


def cronHandler():
    hour = datetime.datetime.now().hour
    reloadDatabase()

    if hour < ACCEPTABLE_NOTIF_HOURS[0] or DEBUG_METHODS == True:
        normalizePosts()

    if hour in ACCEPTABLE_NOTIF_HOURS or DEBUG_METHODS == True:
        sendCronNotification()

    htmlFile = databaseToHtml.generateHtml(db)
    s3uploader.uploadFile(
        htmlFile, 'misc/linkreminder.html', 'files.jameslittle.me')


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
        l.warning(
            f"Database already has {len(db.entries())} entries, cannot reinitialize.")
        return

    for (idx, child) in enumerate(post_list):
        hashes = list(map(lambda x: x["hash"], db.entries()))
        if child.attrib["hash"] in hashes:
            l.debug(f"Duplicate: {child.attrib['href']}")
            duplicates += 1
            continue
        delta = timedelta(days=idx//len(ACCEPTABLE_NOTIF_HOURS))
        punt_until_date = today + delta
        print(punt_until_date)
        addEntryWithPuntDate(child, punt_until_date)
        added += 1
    l.info(f"Inserted {added} entries. {duplicates} duplicates found.")


if __name__ == "__main__":
    db = Database("db.txt")
    if len(db.entries()) == 0:
        initializeDatabase()
    else:
        cronHandler()
    db.write()
