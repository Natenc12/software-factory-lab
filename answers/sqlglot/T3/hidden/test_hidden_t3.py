import unittest

import duckdb

from sqlglot import exp, optimizer

SCHEMA = {"x": {"a": "INT", "b": "INT"}, "y": {"b": "INT", "c": "INT"}}


class TestHiddenT3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = duckdb.connect()
        cls.conn.execute("CREATE TABLE x (a INT, b INT)")
        cls.conn.execute("INSERT INTO x VALUES (1, 1), (2, 2), (3, 3), (4, NULL), (NULL, NULL)")
        cls.conn.execute("CREATE TABLE y (b INT, c INT)")
        cls.conn.execute("INSERT INTO y VALUES (1, 1), (2, 3), (NULL, 3), (5, NULL)")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def assert_same_rows(self, sql):
        optimized = optimizer.optimize(sql, schema=SCHEMA, dialect="duckdb").sql("duckdb")
        expected = self.conn.execute(sql).fetchall()
        actual = self.conn.execute(optimized).fetchall()
        if "ORDER BY" in sql:
            self.assertEqual(actual, expected, optimized)
        else:
            self.assertCountEqual(actual, expected, optimized)

    def test_the_reported_query_keeps_its_rows(self):
        conn = duckdb.connect()
        conn.execute("CREATE TABLE t1 (a INT, b INT)")
        conn.execute("INSERT INTO t1 VALUES (1, 2), (2, 3), (NULL, NULL)")
        conn.execute("CREATE TABLE t2 (a INT, x INT)")
        conn.execute("INSERT INTO t2 VALUES (1, 10), (2, 3)")
        schema = {"t1": {"a": "INT", "b": "INT"}, "t2": {"a": "INT", "x": "INT"}}
        sql = "SELECT a, b FROM t1 WHERE (a IN (SELECT a FROM t2 WHERE t2.x = t1.b)) = FALSE"
        optimized = optimizer.optimize(sql, schema=schema, dialect="duckdb").sql("duckdb")
        self.assertCountEqual(conn.execute(optimized).fetchall(), [(1, 2), (None, None)])

    def test_correlated_in_and_any_keep_false_and_null_apart(self):
        for where in (" WHERE y.c = x.a", " WHERE y.b = x.a"):
            for predicate in (
                f"x.a IN (SELECT y.b FROM y{where})",
                f"x.a = ANY (SELECT y.b FROM y{where})",
            ):
                for sql in (
                    f"SELECT x.a, {predicate} AS r FROM x",
                    f"SELECT x.a, ({predicate}) AND x.a > 1 AS r FROM x",
                    f"SELECT x.a, ({predicate}) OR x.a > 1 AS r FROM x",
                    f"SELECT x.a FROM x WHERE NOT ({predicate})",
                    f"SELECT x.a FROM x WHERE NOT (({predicate}) AND x.a > 1)",
                    f"SELECT x.a FROM x WHERE ({predicate}) IS NULL",
                    f"SELECT x.a FROM x WHERE COALESCE(({predicate}), TRUE)",
                    f"SELECT x.a FROM x WHERE ({predicate}) = FALSE",
                    f"SELECT x.a FROM x WHERE ({predicate}) AND x.a > 1",
                    f"SELECT x.a FROM x WHERE ({predicate}) OR x.a > 1",
                    f"SELECT x.a FROM x JOIN x AS x2 ON x.b = x2.b AND ({predicate}) = FALSE",
                    "SELECT x.a FROM x QUALIFY ROW_NUMBER() OVER (ORDER BY x.a) > 0 "
                    f"AND ({predicate}) = FALSE",
                    f"SELECT x.a FROM x GROUP BY x.a HAVING ({predicate}) IS NULL",
                    f"SELECT x.a FROM x ORDER BY ({predicate}), x.a",
                ):
                    with self.subTest(sql=sql):
                        self.assert_same_rows(sql)

        # A correlated IN used directly as a filter is still unnested
        for sql in (
            "SELECT x.a FROM x WHERE x.a IN (SELECT y.b FROM y WHERE y.c = x.a)",
            "SELECT x.a FROM x WHERE x.a IN (SELECT y.b FROM y WHERE y.c = x.a) AND x.b > 0",
        ):
            with self.subTest(sql=sql):
                optimized = optimizer.optimize(sql, schema=SCHEMA, dialect="duckdb")
                self.assertIsNone(optimized.find(exp.In), optimized.sql("duckdb"))
                self.assert_same_rows(sql)
