#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from operator import itemgetter
import pytest


class Meta(type):
    def __init__(cls, clsname, bases, ns):
        for i, fld in enumerate(ns.get("_fields", [])):
            setattr(cls, fld, property(itemgetter(i)))


class Tuple(tuple, metaclass=Meta):
    def __new__(cls, *args):
        if (n := len(cls._fields)) != len(args):
            raise TypeError(f"{cls} gets exactly {n} args")
        return super().__new__(cls, args)


class Person(Tuple):
    _fields = ["name", "age", "salary"]


def test_person(capsys):
    p = Person("Bob", 37, 12000)
    assert p == ("Bob", 37, 12000)
    assert (p.name, p.age, p.salary) == ("Bob", 37, 12000)
    with pytest.raises(TypeError) as exc:
        p = Person("Bob", 12000)
        assert "gets exactly 3 args" in exc


if __name__ == "__main__":
    p = Person("Bob", 37, 12000)
    print(p)
    print(p.name, p.age, p.salary)
    p = Person("Bob", 12000)
