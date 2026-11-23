from sqlglot import parse_one
from tests.dialects.test_dialect import Validator


class TestHiddenT1Snowflake(Validator):
    dialect = "snowflake"

    def test_top_is_an_ordinary_name(self):
        self.validate_identity("SELECT top FROM t")
        self.validate_identity("SELECT top.x FROM t AS top")
        self.validate_identity("SELECT top, x FROM t")
        self.validate_identity("SELECT top:field FROM t", "SELECT GET_PATH(top, 'field') FROM t")
        # TOP followed by a number is still a row limit
        self.validate_identity("SELECT TOP 5 x FROM t", "SELECT x FROM t LIMIT 5")

    def test_top_with_parentheses_is_a_function_call(self):
        self.validate_identity("SELECT TOP(x) FROM t")
        self.validate_identity("SELECT TOP(5), x FROM t")


class TestHiddenT1Oracle(Validator):
    dialect = "oracle"

    def test_top_is_an_ordinary_name(self):
        self.validate_identity("SELECT top FROM t")
        self.validate_identity("SELECT top, x FROM t")
        self.validate_identity("SELECT TOP(5), x FROM t")

        # Dialects that do have a TOP clause keep it, bind parameters included
        for count in ("1", "%s", "%(n)s"):
            self.assertEqual(
                parse_one(f"SELECT TOP {count} x FROM y", read="redshift").sql("redshift"),
                f"SELECT x FROM y LIMIT {count}",
            )
        self.assertEqual(
            parse_one("SELECT TOP 5 x FROM t", read="tsql").sql("tsql"), "SELECT TOP 5 x FROM t"
        )
        self.assertEqual(
            parse_one("SELECT TOP (@n) x FROM t", read="tsql").sql("tsql"),
            "SELECT TOP (@n) x FROM t",
        )
