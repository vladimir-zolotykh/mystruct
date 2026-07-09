#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from operator import itemgetter


class MetaTuple(type):
    def __init__(cls, clsname, bases, ns):
        fields = ns.get("_fields", [])
        for i, name in enumerate(fields):
            setattr(cls, name, property(itemgetter(i)))


class YaTuple(tuple, metaclass=MetaTuple):
    def __new__(cls, *args):
        if (n := len(cls._fields)) != len(args):
            raise TypeError(f"{cls.__name__} takes {n} arguments")
        return super().__new__(cls, args)


class Point(YaTuple):
    _fields = ["x", "y"]


class Header(YaTuple):
    _fields = ["magic", "x1", "y1", "x2", "y2", "count"]


if __name__ == "__main__":
    p = Point(1, 2)
    print(p.x, p.y)
    h = Header(0x1234, 1, 2, 3, 4, 3)
    print(h[2:4])
