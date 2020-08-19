import datetime
import re

import requests
from bs4 import BeautifulSoup


def get_story(story_id: int):
    data = {}

    req = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
    api_res = req.json()

    req = requests.get(f"https://news.ycombinator.com/item?id={story_id}")
    site_res = req.content

    data["submitter"] = api_res["by"]
    data["score"] = api_res["score"]
    data["submitted_at_utc"] = datetime.datetime.utcfromtimestamp(api_res["time"]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    data["title"] = api_res["title"]
    data["url"] = api_res["url"]

    soup = BeautifulSoup(site_res, features="html.parser")

    def is_tagged_with(tag):
        return any(
            [
                tag in t.find(text=True)
                for t in soup.select("td.title")
                if t.find(text=True) is not None
            ]
        )

    data["is_dupe"] = is_tagged_with("[dupe]")
    data["is_flagged"] = is_tagged_with("[flagged]")

    data["comments"] = []

    comments = soup.select("tr.athing.comtr")
    for comment in comments:
        span_commtext = comment.select("span.commtext")
        data["comments"].append(
            {
                "item_id": comment["id"],
                "commenter": comment.select("a.hnuser")[0].text,
                "comment": None if len(span_commtext) == 0 else span_commtext[0].text,
            }
        )

    return data


def get_main_stories_by_day(date: str):
    stories = []
    details = []
    p = 1
    while True:
        res = requests.get(f"https://news.ycombinator.com/front?day={date}&p={p}")
        soup = BeautifulSoup(res.content, features="html.parser")

        p += 1
        soup = BeautifulSoup(res.content)
        stories += soup.select("tr.athing")
        details += soup.select("td.subtext")

        if len(soup.select("a.morelink")) == 0:
            break

    regex = re.compile(r"\d+\. +(\[dupe\]|\[flagged\])?.+")
    story_tags = [regex.match(story.text.strip()).group(1) for story in stories]

    story_ids = [story["id"] for story in stories]

    story_titles = [story.select("a.storylink")[0].text for story in stories]

    story_urls = [story.select("a.storylink")[0]["href"] for story in stories]

    regex = re.compile(
        r"(\d+) points by ([\w-]+) \d+ \w+ ago .+ (\d+)? (comment|comments|discuss)".replace(
            " ", r"\W+"
        )
    )
    story_etcs = [regex.match(detail.text.strip()).groups() for detail in details]

    stories_zipped = zip(story_ids, story_titles, story_urls, story_etcs, story_tags,)

    stories = []
    for story in stories_zipped:
        comments = story[3][2]
        comments = 0 if comments is None else int(comments)

        url = story[2]
        on_hn = False
        if story[2].startswith("item?id="):
            url = "https://news.ycombinator.com/" + url
            on_hn = True

        stories.append(
            {
                "id": int(story[0]),
                "title": story[1],
                "url": url,
                "points": int(story[3][0]),
                "submitter": story[3][1],
                "comments": comments,
                "tag": story[4],
                "onHN": on_hn,
            }
        )

    return stories
