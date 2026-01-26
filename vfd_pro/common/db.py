from __future__ import annotations
from django.db import connection
from typing import Any, Iterable, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging

sp_logger = logging.getLogger("sp_logger")


def fetch_one_dict(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
    """Executes a SELECT and returns one row as dict (or None)."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))


def fetch_all_dicts(sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
    """Executes a SELECT and returns all rows as list[dict]."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in rows]


def fetch_scalar(
    sql: str, params: Optional[Iterable[Any]] = None, default: Any = None
) -> Any:
    """Executes a SELECT and returns first column of first row."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        row = cursor.fetchone()
        return row[0] if row else default


def callproc_one_dict(proc_name: str, params: list[Any]) -> Optional[dict]:
    """Calls a stored procedure and maps first row result to dict (or None)."""
    with connection.cursor() as cursor:
        cursor.callproc(proc_name, params)
        row = cursor.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))


def callproc_all_dicts(proc_name: str, params: list):

    with connection.cursor() as cursor:
        cursor.callproc(proc_name, params)

        while True:
            if cursor.description:
                cols = [c[0] for c in cursor.description]
                rows = cursor.fetchall()
                if not rows:
                    return []

                out = []
                for r in rows:
                    d = dict(zip(cols, r))
                    d = {k: _json_safe_value(v) for k, v in d.items()}
                    out.append(d)

                return out

            if not cursor.nextset():
                break

    return []


def _json_safe_value(v):
    if v is None:
        return None

    # MySQL BINARY/VARBINARY fields
    if isinstance(v, (bytes, bytearray, memoryview)):

        return bytes(v).hex()

    # datetime/date
    if isinstance(v, (datetime, date)):
        return v.isoformat()

    # Decimal
    if isinstance(v, Decimal):
        return float(v)

    # UUID
    if isinstance(v, UUID):
        return str(v)

    return v
