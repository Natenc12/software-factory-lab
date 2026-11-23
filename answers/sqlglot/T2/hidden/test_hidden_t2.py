from sqlglot import exp
from tests.dialects.test_dialect import Validator


class TestHiddenT2(Validator):
    dialect = "snowflake"

    def test_comment_markers_stay_inside_unquoted_stage_paths(self):
        self.validate_identity("select $1 from @s/a--b", "SELECT $1 FROM @s/a--b")
        self.validate_identity("select $1 from @s/a//b", "SELECT $1 FROM @s/a//b")
        self.validate_identity("select $1 from @s/a/*b", "SELECT $1 FROM @s/a/*b")
        self.validate_identity("copy into t from @s/a--b/c", "COPY INTO t FROM @s/a--b/c")
        for sql in (
            "LIST @s/a--b",
            "LIST @~/a--b",
            'LIST @"my stage"/a--b',
            "SELECT $1 FROM @s/a/*b*/c",
            "SELECT $1 FROM @%t/a--b",
            "SELECT $1 FROM @db.sch.stg/a--b",
            "SELECT * FROM @s/a--b (FILE_FORMAT => 'f')",
            "SELECT * FROM (SELECT $1 FROM @s/a--b) AS x",
            "SELECT * FROM @s/a--b, @t/c--d",
        ):
            with self.subTest(sql):
                self.validate_identity(sql)

        # Unchanged: quoted paths, and comments that follow a path after whitespace
        self.validate_identity("SELECT $1 FROM '@s/a--b'")
        self.validate_identity("SELECT $1 FROM @s/a -- note", "SELECT $1 FROM @s/a /* note */")
        self.validate_identity("LIST @s/a /* keep */")
        self.validate_identity("SELECT $1 FROM @s/a /* keep */ WHERE 1 = 1")

    def test_comment_markers_stay_inside_unquoted_file_uris(self):
        self.validate_identity(
            "put file:///tmp/a--b @s/p", "PUT 'file:///tmp/a--b' @s/p"
        ).assert_is(exp.Put)
        self.validate_identity(
            'PUT file:///dir/a"b.csv @stg', "PUT 'file:///dir/a\"b.csv' @stg"
        ).assert_is(exp.Put)
        self.validate_identity("COPY INTO t FROM 's3://b/p'")
