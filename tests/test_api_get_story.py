import pickle
from pathlib import Path

import requests_mock

from hackernews_api import api


def _test_story_helper(id: int, base_path_assets: Path):
    with open(base_path_assets / "hn_source_code.html") as f_hn:
        hn_html = f_hn.read()
    with open(base_path_assets / "api_response.json") as f_api:
        api_json = f_api.read()
    with open(base_path_assets / "expected_return_value.pickle", "rb") as f_ex:
        ex_obj = pickle.load(f_ex)

    with requests_mock.Mocker() as m:
        m.get(f"https://news.ycombinator.com/item?id={id}", text=hn_html)
        m.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json", text=api_json)
        assert ex_obj == api.get_story(story_id=id)


def test_external_story():
    _test_story_helper(
        id=23885927, base_path_assets=Path("./tests/assets/api_get_story_external_0"),
    )


def test_internal_story():
    _test_story_helper(
        id=23891838, base_path_assets=Path("./tests/assets/api_get_story_internal_0"),
    )
