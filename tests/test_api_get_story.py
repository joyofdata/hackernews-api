import pickle

import requests_mock

from hackernews_api import api


def test_external_story():
    f_hn = open("./tests/assets/api_get_story_external_0/hn_source_code.html")
    f_api = open("./tests/assets/api_get_story_external_0/api_response.json")
    f_ex = open("./tests/assets/api_get_story_external_0/expected_return_value.pickle", "rb")

    with requests_mock.Mocker() as m:
        m.get("https://news.ycombinator.com/item?id=0", text=f_hn.read())
        m.get("https://hacker-news.firebaseio.com/v0/item/0.json", text=f_api.read())
        assert pickle.load(f_ex) == api.get_story(story_id=0)
