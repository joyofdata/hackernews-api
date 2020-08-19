import datetime
import re
from datetime import timezone
from typing import List

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class Comment(BaseModel):
    item_id: int
    commenter: str
    comment: str = None


class Story(BaseModel):
    submitter: str
    score: int
    n_comments: int
    title: str
    url: str
    submitted_at: datetime.datetime = None
    is_dupe: bool = False
    is_flagged: bool = False
    comments: List[Comment] = None


def get_story(story_id: int) -> Story:
    req = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
    api_res = req.json()

    req = requests.get(f"https://news.ycombinator.com/item?id={story_id}")
    site_res = req.content

    submitter = api_res["by"]
    score = api_res["score"]
    submitted_at = datetime.datetime.fromtimestamp(api_res["time"], timezone.utc)
    title = api_res["title"]
    url = api_res["url"]

    soup = BeautifulSoup(site_res, features="html.parser")

    def is_tagged_with(tag):
        return any(
            [
                tag in t.find(text=True)
                for t in soup.select("td.title")
                if t.find(text=True) is not None
            ]
        )

    is_dupe = is_tagged_with("[dupe]")
    is_flagged = is_tagged_with("[flagged]")

    comments = []

    comments_dom = soup.select("tr.athing.comtr")
    for comment in comments_dom:
        span_commtext = comment.select("span.commtext")
        comments.append(
            Comment(
                item_id=comment["id"],
                commenter=comment.select("a.hnuser")[0].text,
                comment=None if len(span_commtext) == 0 else span_commtext[0].text,
            )
        )

    story = Story(
        submitter=submitter,
        score=score,
        n_comments=len(comments),
        title=title,
        url=url,
        submitted_at=submitted_at,
        is_dupe=is_dupe,
        is_flagged=is_flagged,
        comments=comments,
    )

    return story


def get_main_stories_by_day(date: str):
    stories = []
    details = []
    p = 1
    while True:
        res = requests.get(f"https://news.ycombinator.com/front?day={date}&p={p}")
        p += 1
        soup = BeautifulSoup(res.content, features="html.parser")
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
