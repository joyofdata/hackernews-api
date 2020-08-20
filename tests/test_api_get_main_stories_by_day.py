import datetime
import pickle
from pathlib import Path

import requests_mock

from hackernews_api import api


def test_external_story():
    base_dir_assets = Path("./tests/assets/api_get_main_stories_by_day_0")
    date = datetime.date(2020, 7, 19)
    date_str = date.strftime("%Y-%m-%d")

    with open(base_dir_assets / "expected_return_value.pickle", "rb") as f_ex:
        f_ex_unpickled = pickle.load(f_ex)

    with requests_mock.Mocker() as m:
        for p in [1, 2, 3]:
            with open(base_dir_assets / f"hn_source_code_p{p}.html") as f_hn:
                m.get(f"https://news.ycombinator.com/front?day={date_str}&p={p}", text=f_hn.read())
        assert f_ex_unpickled == api.get_main_stories_by_day(date=date)
