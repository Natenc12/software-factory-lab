import unittest

import duckdb

from sqlglot import ErrorLevel, UnsupportedError, transpile

SQL = "SELECT EXISTS(arr, x -> x > 2) FROM t"
SUBQUERY = "SELECT * FROM t WHERE EXISTS(SELECT 1 FROM u WHERE u.id = t.id)"


def to(dialect, sql=SQL, read="spark"):
    return transpile(sql, read=read, write=dialect, unsupported_level=ErrorLevel.RAISE)[0]


class TestHiddenT4(unittest.TestCase):
    def test_spark_family_and_presto_trino(self):
        for dialect in ("spark", "databricks", "hive"):
            with self.subTest(dialect=dialect):
                self.assertEqual(to(dialect), SQL)
        for dialect in ("presto", "trino"):
            with self.subTest(dialect=dialect):
                self.assertEqual(to(dialect), "SELECT ANY_MATCH(arr, x -> x > 2) FROM t")

    def test_duckdb_translation_gives_the_same_answer(self):
        for read in ("spark", "databricks"):
            with self.subTest(read=read):
                sql = to("duckdb", read=read)
                conn = duckdb.connect()
                conn.execute("CREATE TABLE t (id INT, arr INT[])")
                conn.execute("INSERT INTO t VALUES (1, [1, 2, 3]), (2, [1]), (3, []), (4, NULL)")
                ordered = f"SELECT id, r FROM ({sql.replace(' FROM t', ' AS r, id FROM t')}) ORDER BY id"
                self.assertEqual(
                    conn.execute(ordered).fetchall(),
                    [(1, True), (2, False), (3, False), (4, None)],
                    sql,
                )
                conn.close()

    def test_postgres_and_bigquery_keep_the_predicate(self):
        for dialect in ("postgres", "bigquery"):
            with self.subTest(dialect=dialect):
                sql = to(dialect)
                self.assertIn("x > 2", sql)
                self.assertNotIn("EXISTS(arr)", sql)

    def test_dialects_without_array_filtering_report_it(self):
        with self.assertRaises(UnsupportedError):
            to("mysql")

        # EXISTS over a subquery is untouched everywhere
        for dialect in ("duckdb", "postgres", "bigquery", "presto", "mysql", "spark"):
            with self.subTest(dialect=dialect):
                self.assertEqual(to(dialect, SUBQUERY), SUBQUERY)
