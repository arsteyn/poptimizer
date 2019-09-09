from datetime import date

import pandas as pd
import pytest

import poptimizer.store.utils_new
from poptimizer.config import POptimizerError
from poptimizer.store import manager_new, DATE
from poptimizer.store.mongo import MONGO_CLIENT


@pytest.fixture("module", autouse=True, name="manager")
def drop_test_db():
    MONGO_CLIENT.drop_database("test")
    yield
    MONGO_CLIENT.drop_database("test")


class SimpleManager(manager_new.AbstractManager):
    LOAD = [{DATE: 1, "col1": 1, "col2": 10}, {DATE: 2, "col1": 2, "col2": 15}]
    UPDATE = [{DATE: 2, "col1": 2, "col2": 15}, {DATE: 4, "col1": 5, "col2": 5}]

    def __init__(self, create_from_scratch=False, validate_last=True):
        super().__init__(
            collection="simple",
            db="test",
            create_from_scratch=create_from_scratch,
            validate_last=validate_last,
        )

    def _download(self, name, last_index):
        if last_index is None or not self._validate_last:
            return self.LOAD
        return self.UPDATE


def test_create():
    manager = SimpleManager()
    # noinspection PyProtectedMember
    collection = manager._collection

    time0 = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ).astimezone(None)
    assert collection.find_one({"_id": "AKRN"}) is None

    data = manager["AKRN"]
    assert isinstance(data, pd.DataFrame)
    assert data.equals(
        pd.DataFrame(data={"col1": [1, 2], "col2": [10, 15]}, index=[1, 2])
    )
    assert collection.find_one({"_id": "AKRN"})["timestamp"] > time0


def test_no_update():
    manager = SimpleManager()
    # noinspection PyProtectedMember
    collection = manager._collection

    time0 = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ).astimezone(None)
    assert collection.find_one({"_id": "AKRN"})["timestamp"] < time0

    data = manager["AKRN"]
    assert isinstance(data, pd.DataFrame)
    assert data.equals(
        pd.DataFrame(data={"col1": [1, 2], "col2": [10, 15]}, index=[1, 2])
    )
    assert collection.find_one({"_id": "AKRN"})["timestamp"] < time0


@pytest.fixture(scope="module")
def next_week_date():
    timestamp = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ)
    timestamp += pd.DateOffset(days=7)
    timestamp = timestamp.astimezone(None)
    return timestamp


def test_update(monkeypatch, next_week_date):
    manager = SimpleManager()
    # noinspection PyProtectedMember
    collection = manager._collection
    monkeypatch.setattr(manager, "LAST_HISTORY_DATE", next_week_date)

    time0 = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ).astimezone(None)
    assert collection.find_one({"_id": "AKRN"})["timestamp"] < time0

    data = manager["AKRN"]
    assert isinstance(data, pd.DataFrame)
    assert data.equals(
        pd.DataFrame(data={"col1": [1, 2, 5], "col2": [10, 15, 5]}, index=[1, 2, 4])
    )
    assert collection.find_one({"_id": "AKRN"})["timestamp"] > time0


def test_data_create_from_scratch(monkeypatch, next_week_date):
    manager = SimpleManager(create_from_scratch=True)
    # noinspection PyProtectedMember
    collection = manager._collection
    monkeypatch.setattr(manager, "LAST_HISTORY_DATE", next_week_date)

    time0 = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ).astimezone(None)
    assert collection.find_one({"_id": "AKRN"})["timestamp"] < time0

    data = manager["AKRN"]
    assert isinstance(data, pd.DataFrame)
    assert data.equals(
        pd.DataFrame(data={"col1": [1, 2], "col2": [10, 15]}, index=[1, 2])
    )
    assert collection.find_one({"_id": "AKRN"})["timestamp"] > time0


def test_index_non_unique(monkeypatch):
    manager = SimpleManager()
    monkeypatch.setattr(manager, "LOAD", [{DATE: 1, "col1": 1}, {DATE: 1, "col1": 2}])

    with pytest.raises(POptimizerError) as error:
        # noinspection PyStatementEffect
        manager["RTKM"]
    assert str(error.value) == "Индекс test.simple.RTKM не уникальный"


def test_index_non_increasing(monkeypatch):
    manager = SimpleManager()
    monkeypatch.setattr(manager, "LOAD", [{DATE: 2, "col1": 1}, {DATE: 1, "col1": 2}])

    with pytest.raises(POptimizerError) as error:
        # noinspection PyStatementEffect
        manager["GAZP"]
    assert str(error.value) == "Индекс test.simple.GAZP не возрастает"


def test_validate_all_too_short(monkeypatch, next_week_date):
    manager = SimpleManager(validate_last=False)
    monkeypatch.setattr(manager, "LAST_HISTORY_DATE", next_week_date)
    monkeypatch.setattr(manager, "LOAD", [{DATE: 1, "col1": 2}])

    with pytest.raises(POptimizerError) as error:
        # noinspection PyStatementEffect
        manager["AKRN"]
    assert str(error.value) == "Новые 1 короче старых 2 данных test.simple.AKRN"


def test_data_not_stacks(monkeypatch, next_week_date):
    manager = SimpleManager()
    monkeypatch.setattr(manager, "LAST_HISTORY_DATE", next_week_date)
    monkeypatch.setattr(manager, "UPDATE", [{DATE: 4, "col1": 5, "col2": 5}])

    with pytest.raises(POptimizerError) as error:
        # noinspection PyStatementEffect
        manager["AKRN"]
    assert (
        str(error.value)
        == "Новые {'DATE': 4, 'col1': 5, 'col2': 5} не соответствуют старым "
        "{'DATE': 2, 'col1': 2, 'col2': 15} данным test.simple.AKRN"
    )


def test_validate_all(monkeypatch, next_week_date):
    manager = SimpleManager(validate_last=False)
    monkeypatch.setattr(manager, "LAST_HISTORY_DATE", next_week_date)
    fake_load = [
        {DATE: 1, "col1": 1, "col2": 10},
        {DATE: 2, "col1": 2, "col2": 15},
        {DATE: 7, "col1": 9, "col2": 11},
    ]
    monkeypatch.setattr(manager, "LOAD", fake_load)
    # noinspection PyProtectedMember
    collection = manager._collection

    time0 = pd.Timestamp.now(poptimizer.store.utils_new.MOEX_TZ).astimezone(None)
    assert collection.find_one({"_id": "AKRN"})["timestamp"] < time0

    data = manager["AKRN"]
    assert isinstance(data, pd.DataFrame)
    assert data.equals(
        pd.DataFrame(data={"col1": [1, 2, 9], "col2": [10, 15, 11]}, index=[1, 2, 7])
    )
    assert collection.find_one({"_id": "AKRN"})["timestamp"] > time0


def test_data_formatter():
    data = [{DATE: "2011-02-12", "col1": 1}, {DATE: "2019-09-09", "col1": 2}]
    formatter = {DATE: date.fromisoformat}
    result = [{DATE: date(2011, 2, 12), "col1": 1}, {DATE: date(2019, 9, 9), "col1": 2}]
    assert manager_new.data_formatter(data, formatter) == result
