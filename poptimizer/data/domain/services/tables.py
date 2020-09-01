"""Доменные службы, ответственные за обновление таблиц."""
from typing import Optional

from poptimizer.data.domain import model
from poptimizer.data.domain.services import trading_day


def update(
    table: model.Table,
    helper: Optional[model.Table],
    force: bool = False,
) -> None:
    """Обновляет таблицу."""
    end_of_trading_day = trading_day.get_end(helper)
    if force or table.need_update(end_of_trading_day):
        table.update()


def force_update(
    table: model.Table,
    helper: Optional[model.Table],
) -> None:
    """Принудительно обновляет таблицу."""
    update(table, helper, force=True)
