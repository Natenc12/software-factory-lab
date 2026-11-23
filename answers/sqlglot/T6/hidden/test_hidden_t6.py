import unittest

import duckdb

from sqlglot import parse_one, transpile
from sqlglot.optimizer.annotate_types import annotate_types


def to(sql, read, write):
    return transpile(sql, read=read, write=write)[0]


def run_duckdb(sql):
    conn = duckdb.connect()
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


SIM = "SELECT VECTOR_COSINE_SIMILARITY(a, b) FROM t"


class TestHiddenT6(unittest.TestCase):
    def test_snowflake_similarity_stays_a_similarity(self):
        self.assertEqual(to(SIM, "snowflake", "snowflake"), SIM)
        self.assertEqual(
            to(SIM, "snowflake", "duckdb"), "SELECT LIST_COSINE_SIMILARITY(a, b) FROM t"
        )
        self.assertEqual(
            to(SIM, "snowflake", "bigquery"), "SELECT (1 - COSINE_DISTANCE(a, b)) FROM t"
        )
        self.assertEqual(
            to(SIM, "snowflake", "clickhouse"), "SELECT (1 - cosineDistance(a, b)) FROM t"
        )
        self.assertEqual(
            to("SELECT VECTOR_COSINE_SIMILARITY(a, b) * 2 FROM t", "snowflake", "bigquery"),
            "SELECT (1 - COSINE_DISTANCE(a, b)) * 2 FROM t",
        )

        duck = to("SELECT VECTOR_COSINE_SIMILARITY([1.0, 0.0], [1.0, 1.0])", "snowflake", "duckdb")
        self.assertAlmostEqual(run_duckdb(duck), 0.7071067811865475, places=9)

        # Snowflake still types it as a DOUBLE
        expression = annotate_types(
            parse_one("SELECT VECTOR_COSINE_SIMILARITY(a, b) AS s FROM t", read="snowflake"),
            dialect="snowflake",
        )
        self.assertTrue(expression.selects[0].type.is_type("double"))

    def test_distance_is_written_as_a_distance_for_snowflake(self):
        expected = "SELECT (1 - VECTOR_COSINE_SIMILARITY(a, b)) FROM t"
        self.assertEqual(
            to("SELECT COSINE_DISTANCE(a, b) FROM t", "bigquery", "snowflake"), expected
        )
        self.assertEqual(
            to("SELECT cosineDistance(a, b) FROM t", "clickhouse", "snowflake"), expected
        )
        self.assertEqual(
            to("SELECT LIST_COSINE_DISTANCE(a, b) FROM t", "duckdb", "snowflake"), expected
        )
        self.assertEqual(
            to("SELECT COSINE_DISTANCE(a, b) * 2 FROM t", "bigquery", "snowflake"),
            "SELECT (1 - VECTOR_COSINE_SIMILARITY(a, b)) * 2 FROM t",
        )

        # Distance between dialects that have it is unchanged
        self.assertEqual(
            to("SELECT COSINE_DISTANCE(a, b) FROM t", "bigquery", "duckdb"),
            "SELECT LIST_COSINE_DISTANCE(a, b) FROM t",
        )
        duck = to("SELECT COSINE_DISTANCE([1.0, 0.0], [1.0, 1.0])", "bigquery", "duckdb")
        self.assertAlmostEqual(run_duckdb(duck), 0.29289321881345254, places=9)

    def test_duckdb_list_cosine_similarity(self):
        sql = "SELECT LIST_COSINE_SIMILARITY(a, b) FROM t"
        self.assertEqual(to(sql, "duckdb", "duckdb"), sql)
        self.assertEqual(to(sql, "duckdb", "snowflake"), SIM)
        self.assertEqual(to(sql, "duckdb", "bigquery"), "SELECT (1 - COSINE_DISTANCE(a, b)) FROM t")

        # Unchanged: DuckDB's fixed-size ARRAY_ variant, and the default dialect's spelling
        array_sql = "SELECT ARRAY_COSINE_SIMILARITY(a, b) FROM t"
        self.assertEqual(to(array_sql, "duckdb", "duckdb"), array_sql)
        default_sql = "SELECT COSINE_SIMILARITY(a, b) FROM t"
        self.assertEqual(to(default_sql, "", ""), default_sql)
