import requests
from bs4 import BeautifulSoup
import datetime


def get_story(story_id: int):
    data = {}

    req = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
    api_res = req.json()

    req = requests.get(f"https://news.ycombinator.com/item?id={story_id}")
    site_res = req.content

    data["submitter"] = api_res["by"]
    data["score"] = api_res["score"]
    data["submitted_at_utc"] = datetime.datetime.utcfromtimestamp(api_res["time"]).strftime("%Y-%m-%d %H:%M:%S")
    data["title"] = api_res["title"]
    data["url"] = api_res["url"]

    soup = BeautifulSoup(site_res, features="html.parser")

    def is_tagged_with(tag):
        return any([tag in t.find(text=True) for t in soup.select("td.title") if t.find(text=True) is not None])

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
