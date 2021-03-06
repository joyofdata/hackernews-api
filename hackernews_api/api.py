import datetime
import html
import re
from datetime import timezone
from typing import List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class Comment(BaseModel):
    item_id: int
    commenter: str
    comment: Optional[str] = None


class Story(BaseModel):
    item_id: int
    submitter: Optional[str]
    score: Optional[int]
    n_comments: Optional[int]
    title: str
    url: str
    on_hn: Optional[bool] = None
    text: Optional[str] = None
    submitted_at: Union[datetime.datetime, datetime.date]
    is_dupe: Optional[bool] = False
    is_flagged: Optional[bool] = False
    comments: Optional[List[Comment]] = None


def get_story(story_id: int) -> Story:
    req = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
    api_res = req.json()

    req = requests.get(f"https://news.ycombinator.com/item?id={story_id}")
    site_res = req.content

    submitter = api_res["by"]
    score = api_res["score"]
    submitted_at = datetime.datetime.fromtimestamp(api_res["time"], timezone.utc)
    title = api_res["title"]

    text = None
    if "text" in api_res:
        text = html.unescape(api_res["text"])

    soup = BeautifulSoup(site_res, features="html.parser")

    url = soup.select("a.storylink")[0]["href"]
    on_hn = False
    if url.startswith("item?id="):
        url = "https://news.ycombinator.com/" + url
        on_hn = True

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
        item_id=story_id,
        submitter=submitter,
        score=score,
        n_comments=len(comments),
        title=title,
        url=url,
        on_hn=on_hn,
        text=text,
        submitted_at=submitted_at,
        is_dupe=is_dupe,
        is_flagged=is_flagged,
        comments=comments,
    )

    return story


def get_main_stories_by_day(date: datetime.date) -> List[Story]:
    stories = []
    details = []
    p = 1
    with requests.Session() as session:
        while True:
            date_str = date.strftime("%Y-%m-%d")
            res = session.get(f"https://news.ycombinator.com/front?day={date_str}&p={p}")
            p += 1
            soup = BeautifulSoup(res.content, features="html.parser")
            stories += soup.select("tr.athing")
            details += soup.select("td.subtext")

            if len(soup.select("a.morelink")) == 0:
                break

    regex = re.compile(r"\d+\. +(\[dupe\]|\[flagged\])?.+")
    story_tags: List[Optional[str]] = []
    for story in stories:
        m = regex.match(story.text.strip())
        if m is None:
            story_tags.append(None)
        else:
            story_tags.append(m.group(1))

    story_ids = [story["id"] for story in stories]

    story_titles = [story.select("a.storylink")[0].text for story in stories]

    story_urls = [story.select("a.storylink")[0]["href"] for story in stories]

    regex = re.compile(r"(\d+) points by ([\w-]+) \d+ \w+ ago[^0-9]+(\d+)?.+".replace(" ", r"\W+"))
    story_etcs: List[Tuple[Optional[str], ...]] = []
    for detail in details:
        m = regex.match(detail.text.strip())
        if m is None:
            story_etcs.append((None, None, None))
        else:
            story_etcs.append(tuple(m.groups()))

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
            Story(
                item_id=int(story[0]),
                title=story[1],
                url=url,
                on_hn=on_hn,
                text=None,
                submitted_at=date,
                score=int(story[3][0]),
                submitter=story[3][1],
                n_comments=comments,
                is_dupe=(story[4] == "[dupe]"),
                is_flagged=(story[4] == "[flagged]"),
            )
        )

    return stories
