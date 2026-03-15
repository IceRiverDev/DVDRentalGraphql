"""Unit tests for the scalar filter apply-helpers in app.graphql.filters.shared.

These tests are pure Python – no database connection required.  We build a
minimal SQLAlchemy Table, apply a filter, and inspect the compiled WHERE clause.
"""
from __future__ import annotations

import pytest
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, select

from app.graphql.filters.shared import (
    DateFilter,
    DateTimeFilter,
    FloatFilter,
    IntFilter,
    StringFilter,
    apply_date_filter,
    apply_datetime_filter,
    apply_float_filter,
    apply_int_filter,
    apply_string_filter,
)

# ---------------------------------------------------------------------------
# Minimal SQLAlchemy table used as a test fixture
# ---------------------------------------------------------------------------

_meta = MetaData()
_t = Table(
    "t",
    _meta,
    Column("id", Integer),
    Column("name", String),
    Column("score", Float),
)
id_col = _t.c.id
name_col = _t.c.name
score_col = _t.c.score


def _sql(q) -> str:
    """Compile a query to its SQL string with literal bind values."""
    return str(q.compile(compile_kwargs={"literal_binds": True}))


# ---------------------------------------------------------------------------
# StringFilter
# ---------------------------------------------------------------------------

class TestApplyStringFilter:
    def _q(self, f: StringFilter) -> str:
        return _sql(apply_string_filter(select(_t), name_col, f))

    def test_none_filter_adds_no_where(self):
        q = apply_string_filter(select(_t), name_col, None)
        assert q.whereclause is None

    def test_eq(self):
        sql = self._q(StringFilter(eq="hello"))
        assert "= 'hello'" in sql

    def test_neq(self):
        sql = self._q(StringFilter(neq="hello"))
        assert "!= 'hello'" in sql

    def test_like(self):
        sql = self._q(StringFilter(like="%test%"))
        assert "LIKE '%test%'" in sql

    def test_ilike(self):
        sql = self._q(StringFilter(ilike="%Test%"))
        # SQLAlchemy compiles ILIKE as lower(col) LIKE lower(pattern) on backends
        # that don't natively support ILIKE (e.g. SQLite).  Either form is correct.
        assert "ILIKE '%Test%'" in sql or "lower(" in sql.lower()

    def test_contains(self):
        sql = self._q(StringFilter(contains="love"))
        assert "%love%" in sql

    def test_starts_with(self):
        sql = self._q(StringFilter(starts_with="ac"))
        assert "ac%" in sql

    def test_ends_with(self):
        sql = self._q(StringFilter(ends_with="tion"))
        assert "%tion" in sql

    def test_in(self):
        sql = self._q(StringFilter(in_=["a", "b", "c"]))
        assert "IN" in sql.upper()
        assert "'a'" in sql

    def test_is_null_true(self):
        sql = self._q(StringFilter(is_null=True))
        assert "IS NULL" in sql.upper()

    def test_is_null_false(self):
        sql = self._q(StringFilter(is_null=False))
        assert "IS NOT NULL" in sql.upper()

    def test_multiple_operators_combined(self):
        # Both conditions should appear (AND-ed)
        sql = self._q(StringFilter(starts_with="ac", ends_with="my"))
        assert "ac%" in sql
        assert "%my" in sql


# ---------------------------------------------------------------------------
# IntFilter
# ---------------------------------------------------------------------------

class TestApplyIntFilter:
    def _q(self, f: IntFilter) -> str:
        return _sql(apply_int_filter(select(_t), id_col, f))

    def test_none_filter_adds_no_where(self):
        q = apply_int_filter(select(_t), id_col, None)
        assert q.whereclause is None

    def test_eq(self):
        sql = self._q(IntFilter(eq=42))
        assert "= 42" in sql

    def test_neq(self):
        sql = self._q(IntFilter(neq=42))
        assert "!= 42" in sql

    def test_gt(self):
        sql = self._q(IntFilter(gt=10))
        assert "> 10" in sql

    def test_gte(self):
        sql = self._q(IntFilter(gte=10))
        assert ">= 10" in sql

    def test_lt(self):
        sql = self._q(IntFilter(lt=100))
        assert "< 100" in sql

    def test_lte(self):
        sql = self._q(IntFilter(lte=100))
        assert "<= 100" in sql

    def test_range_combined(self):
        sql = self._q(IntFilter(gte=90, lte=120))
        assert ">= 90" in sql
        assert "<= 120" in sql

    def test_in(self):
        sql = self._q(IntFilter(in_=[1, 2, 3]))
        assert "IN" in sql.upper()
        assert "1" in sql

    def test_is_null_true(self):
        sql = self._q(IntFilter(is_null=True))
        assert "IS NULL" in sql.upper()

    def test_is_null_false(self):
        sql = self._q(IntFilter(is_null=False))
        assert "IS NOT NULL" in sql.upper()


# ---------------------------------------------------------------------------
# FloatFilter
# ---------------------------------------------------------------------------

class TestApplyFloatFilter:
    def _q(self, f: FloatFilter) -> str:
        return _sql(apply_float_filter(select(_t), score_col, f))

    def test_none_filter_adds_no_where(self):
        q = apply_float_filter(select(_t), score_col, None)
        assert q.whereclause is None

    def test_eq(self):
        sql = self._q(FloatFilter(eq=4.99))
        assert "4.99" in sql

    def test_gte(self):
        sql = self._q(FloatFilter(gte=2.0))
        assert ">= 2.0" in sql

    def test_lte(self):
        sql = self._q(FloatFilter(lte=9.99))
        assert "<= 9.99" in sql

    def test_gt_lt(self):
        sql = self._q(FloatFilter(gt=1.0, lt=5.0))
        assert "> 1.0" in sql
        assert "< 5.0" in sql


# ---------------------------------------------------------------------------
# DateTimeFilter
# ---------------------------------------------------------------------------

class TestApplyDateTimeFilter:
    def _q(self, f: DateTimeFilter) -> str:
        return _sql(apply_datetime_filter(select(_t), id_col, f))

    def test_none_filter_adds_no_where(self):
        q = apply_datetime_filter(select(_t), id_col, None)
        assert q.whereclause is None

    def test_gte(self):
        sql = self._q(DateTimeFilter(gte="2007-04-01T00:00:00"))
        assert ">=" in sql
        assert "2007" in sql

    def test_lte(self):
        sql = self._q(DateTimeFilter(lte="2007-04-30T23:59:59"))
        assert "<=" in sql
        assert "2007" in sql

    def test_invalid_iso_raises(self):
        with pytest.raises(ValueError):
            self._q(DateTimeFilter(gte="not-a-date"))

    def test_is_null_true(self):
        sql = self._q(DateTimeFilter(is_null=True))
        assert "IS NULL" in sql.upper()


# ---------------------------------------------------------------------------
# DateFilter
# ---------------------------------------------------------------------------

class TestApplyDateFilter:
    def _q(self, f: DateFilter) -> str:
        return _sql(apply_date_filter(select(_t), id_col, f))

    def test_none_filter_adds_no_where(self):
        q = apply_date_filter(select(_t), id_col, None)
        assert q.whereclause is None

    def test_eq(self):
        sql = self._q(DateFilter(eq="2020-01-15"))
        assert "2020" in sql

    def test_range(self):
        sql = self._q(DateFilter(gte="2020-01-01", lte="2020-12-31"))
        assert ">=" in sql
        assert "<=" in sql
        assert "2020" in sql

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            self._q(DateFilter(eq="not-a-date"))
