#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from collections.abc import Iterable
from itertools import chain
from dataclasses import dataclass, field, fields
import struct

POLYGONS = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 6.3), (1.2, 0.5), (4.6, 9.2)],
]


@dataclass
class StarIter:
    def __iter__(self):
        for s in fields(self):
            if isinstance((a := getattr(self, s.name)), Iterable):
                yield from a
            else:
                yield a


@dataclass
class Point(StarIter):
    x: float = 0.0
    y: float = 0.0


@dataclass
class Bbox(StarIter):
    p1: Point = field(default_factory=Point)
    p2: Point = field(default_factory=Point)


def get_bbox(poly=POLYGONS) -> Bbox:
    p1 = Point()
    p1.x = min(x for x, _ in chain(*poly))
    p1.y = min(y for _, y in chain(*poly))
    p2 = Point()
    p2.x = max(x for x, _ in chain(*poly))
    p2.y = max(y for _, y in chain(*poly))
    return Bbox(p1, p2)


@dataclass
class Header(StarIter):
    magic: int
    x1: float
    y1: float
    x2: float
    y2: float
    len: int

    def write(self, f) -> None:
        f.write(struct.pack("<iddddi", *self))

    def read(self, f) -> None:
        self.magic, self.x1, self.y1, self.x2, self.y2, self.len = f.read(
            struct.calcsize("<iddddi")
        )


def write_polygons() -> None:
    bb = get_bbox()
    h = Header(0x1234, *bb, len(POLYGONS))
    with open("polygons.dat", "wb") as f:
        h.write(f)


if __name__ == "__main__":
    write_polygons()
