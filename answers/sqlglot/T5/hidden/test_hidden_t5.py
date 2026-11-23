from sqlglot import ErrorLevel, ParseError, UnsupportedError, exp, parse_one, transpile
from tests.dialects.test_dialect import Validator

ACTIONS = ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK")


class TestHiddenT5(Validator):
    dialect = "sqlite"

    def test_update_or_round_trips_in_sqlite(self):
        for action in ACTIONS:
            with self.subTest(action=action):
                update = self.validate_identity(f"UPDATE OR {action} t SET b = 'x' WHERE id = 1")
                self.assertIsInstance(update, exp.Update)
        self.validate_identity("update or ignore t set b = 'x'", "UPDATE OR IGNORE t SET b = 'x'")
        self.validate_identity(
            "UPDATE OR REPLACE t AS u SET b = 'x' FROM s WHERE u.id = s.id RETURNING *"
        )

    def test_update_or_in_the_default_dialect(self):
        sql = "UPDATE OR IGNORE t SET b = 'x'"
        self.assertEqual(parse_one(sql).sql(), sql)
        self.assertEqual(transpile(sql, read="sqlite", write="")[0], sql)

    def test_dialects_without_update_or_report_it(self):
        for dialect in ("postgres", "mysql", "teradata"):
            with self.subTest(dialect=dialect):
                with self.assertRaises(UnsupportedError):
                    transpile(
                        "UPDATE OR IGNORE t SET b = 'x'",
                        read="sqlite",
                        write=dialect,
                        unsupported_level=ErrorLevel.RAISE,
                    )
        # A plain UPDATE is unaffected
        self.assertEqual(
            transpile("UPDATE t SET b = 'x'", read="sqlite", write="postgres")[0],
            "UPDATE t SET b = 'x'",
        )

    def test_update_or_without_an_action_is_an_error(self):
        with self.assertRaises(ParseError):
            parse_one("UPDATE OR t SET b = 'x'", read="sqlite")
        # INSERT OR is unchanged
        self.validate_identity("INSERT OR REPLACE INTO t VALUES (1)")
        self.validate_identity("UPDATE OR REPLACE t SET b = 'x'")
