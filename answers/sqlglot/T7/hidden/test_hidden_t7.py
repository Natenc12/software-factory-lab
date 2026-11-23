import unittest

from sqlglot import parse_one
from sqlglot.optimizer import optimize
from sqlglot.optimizer.simplify import simplify


def simplified(sql, **kwargs):
    return simplify(parse_one(sql), **kwargs).sql()


class TestHiddenT7(unittest.TestCase):
    def test_null_arguments_are_dropped(self):
        for sql, expected in (
            ("COALESCE(NULL, x)", "x"),
            ("COALESCE(x, NULL)", "x"),
            ("COALESCE(x, NULL, y)", "COALESCE(x, y)"),
            ("COALESCE(NULL, NULL, x, NULL, y)", "COALESCE(x, y)"),
            ("COALESCE(NULL, NULL)", "NULL"),
            ("SELECT COALESCE(NULL, a) AS b FROM t", "SELECT a AS b FROM t"),
            ("COALESCE(x, y)", "COALESCE(x, y)"),
        ):
            with self.subTest(sql=sql):
                self.assertEqual(simplified(sql), expected)
                self.assertEqual(simplified(sql, coalesce_simplification=True), expected)

        self.assertEqual(
            optimize(
                "SELECT COALESCE(NULL, a, NULL, b) AS c FROM t",
                schema={"t": {"a": "INT", "b": "INT"}},
            ).sql(),
            'SELECT COALESCE("t"."a", "t"."b") AS "c" FROM "t" AS "t"',
        )

        # COALESCE used as a Spark partitioning hint is left alone
        hint = "SELECT /*+ COALESCE(3) */ * FROM t"
        self.assertEqual(simplify(parse_one(hint, read="spark")).sql("spark"), hint)

    def test_arguments_after_a_non_null_constant_are_dropped(self):
        for sql, expected in (
            ("COALESCE(x, 0, y)", "COALESCE(x, 0)"),
            ("COALESCE(NULL, 0, y)", "0"),
            ("COALESCE(x, 'a', NULL, y)", "COALESCE(x, 'a')"),
            ("COALESCE(x, NULL, 0, y, NULL)", "COALESCE(x, 0)"),
        ):
            with self.subTest(sql=sql):
                self.assertEqual(simplified(sql), expected)
