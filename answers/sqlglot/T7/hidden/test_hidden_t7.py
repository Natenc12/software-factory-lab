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
        # Through optimize() with same-typed columns, so a fix that only drops the arguments when
        # the result type cannot change passes as well as one that always drops them
        schema = {"t": {"a": "INT", "b": "INT", "s": "VARCHAR", "u": "VARCHAR"}}
        for sql, expected in (
            ("SELECT COALESCE(a, 0, b) AS c FROM t", 'COALESCE("t"."a", 0)'),
            ("SELECT COALESCE(NULL, 0, b) AS c FROM t", "0"),
            ("SELECT COALESCE(s, 'a', NULL, u) AS c FROM t", """COALESCE("t"."s", 'a')"""),
            ("SELECT COALESCE(a, NULL, 0, b, NULL) AS c FROM t", 'COALESCE("t"."a", 0)'),
        ):
            with self.subTest(sql=sql):
                self.assertEqual(
                    optimize(sql, schema=schema).sql(), f'SELECT {expected} AS "c" FROM "t" AS "t"'
                )
