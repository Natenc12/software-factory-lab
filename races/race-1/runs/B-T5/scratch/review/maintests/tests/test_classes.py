import sqlite3

import pytest

from lab import classes


def test_create_and_get_class(conn):
    klass = classes.create_class(conn, "  Chemistry ", "Atoms bond.")
    assert klass.name == "Chemistry"
    assert classes.get_class(conn, klass.id) == klass


def test_class_needs_a_name(conn):
    with pytest.raises(ValueError):
        classes.create_class(conn, "   ")


def test_class_names_are_unique(conn):
    classes.create_class(conn, "Chemistry")
    with pytest.raises(sqlite3.IntegrityError):
        classes.create_class(conn, "Chemistry")


def test_list_classes_sorted_by_name(conn):
    classes.create_class(conn, "Physics")
    classes.create_class(conn, "Art")
    assert [c.name for c in classes.list_classes(conn)] == ["Art", "Physics"]


def test_missing_class_raises(conn):
    with pytest.raises(LookupError):
        classes.get_class(conn, 42)


def test_set_material(conn, biology):
    klass, _, _ = biology
    assert classes.set_material(conn, klass.id, "New notes.").material == "New notes."


def test_enrol_and_list_students(conn, biology):
    klass, ada, ben = biology
    assert classes.list_students(conn, klass.id) == [ada, ben]
    assert ada.class_id == klass.id


def test_student_names_are_unique_within_a_class_only(conn, biology):
    klass, _, _ = biology
    with pytest.raises(sqlite3.IntegrityError):
        classes.enrol_student(conn, klass.id, "Ada")
    other = classes.create_class(conn, "Art")
    assert classes.enrol_student(conn, other.id, "Ada").class_id == other.id


def test_enrol_in_missing_class_raises(conn):
    with pytest.raises(LookupError):
        classes.enrol_student(conn, 42, "Ada")
