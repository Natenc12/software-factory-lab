import sys
import unittest
from importlib import metadata
from unittest import mock

from sqlglot import parse_one
from sqlglot.optimizer.simplify import simplify

FOLDED = {
    "DATE '2021-01-01' + INTERVAL '1' MONTH": "CAST('2021-02-01' AS DATE)",
    "DATE '2021-01-31' + INTERVAL '1' MONTH": "CAST('2021-02-28' AS DATE)",
    "DATE '2024-02-29' + INTERVAL '1' YEAR": "CAST('2025-02-28' AS DATE)",
    "DATE '2021-03-31' - INTERVAL '1' MONTH": "CAST('2021-02-28' AS DATE)",
    "DATE '2021-01-31' + INTERVAL '1' QUARTER": "CAST('2021-04-30' AS DATE)",
    "DATE '2021-01-01' + INTERVAL '-1' MONTH": "CAST('2020-12-01' AS DATE)",
    "DATE '2021-01-01' + INTERVAL '2' WEEK": "CAST('2021-01-15' AS DATE)",
    "DATE '2021-01-01' + INTERVAL '3' DAY": "CAST('2021-01-04' AS DATE)",
    "CAST('2021-01-31 10:00:00' AS DATETIME) + INTERVAL '1' MONTH": "CAST('2021-02-28 10:00:00' AS DATETIME)",
    "CAST('2021-01-01 10:00:00' AS DATETIME) + INTERVAL '90' MINUTE": "CAST('2021-01-01 11:30:00' AS DATETIME)",
    "x > DATE '2021-01-31' + INTERVAL '1' MONTH": "x > CAST('2021-02-28' AS DATE)",
    "DATE_TRUNC('month', x) = DATE '2021-01-01'": "x < CAST('2021-02-01' AS DATE) AND x >= CAST('2021-01-01' AS DATE)",
}

NO_DATEUTIL = {"dateutil": None, "dateutil.relativedelta": None}


def simplified(sql):
    return simplify(parse_one(sql)).sql()


class TestHiddenT8(unittest.TestCase):
    def test_date_arithmetic_folds_without_dateutil(self):
        with mock.patch.dict(sys.modules, NO_DATEUTIL):
            for sql, expected in FOLDED.items():
                with self.subTest(sql=sql):
                    self.assertEqual(simplified(sql), expected)

        # sqlglot itself still requires nothing at install time
        required = [r for r in metadata.requires("sqlglot") or [] if "extra ==" not in r]
        self.assertEqual(required, [])

    def test_same_result_with_and_without_dateutil(self):
        for sql in FOLDED:
            with self.subTest(sql=sql):
                with_dateutil = simplified(sql)
                with mock.patch.dict(sys.modules, NO_DATEUTIL):
                    self.assertEqual(simplified(sql), with_dateutil)
