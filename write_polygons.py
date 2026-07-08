#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os
from typing import Self, BinaryIO, TYPE_CHECKING
from collections.abc import Iterable
from itertools import chain
from dataclasses import dataclass, field, fields
import struct

PointType = tuple[float, float]
PolygonType = list[PointType]
PolygonsType = list[PolygonType]
POLYGONS: PolygonsType = [
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


def get_bbox(poly: PolygonsType = POLYGONS) -> Bbox:
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

    def write(self, f: BinaryIO) -> None:
        f.write(struct.pack("<iddddi", *self))

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        return cls(*struct.unpack("<iddddi", f.read(struct.calcsize("<iddddi"))))


def write_polygons() -> None:
    bb = get_bbox()
    if TYPE_CHECKING:
        h = Header(0x1234, bb.p1.x, bb.p1.y, bb.p2.y, bb.p2.y, len(POLYGONS))
    else:
        h = Header(0x1234, *bb, len(POLYGONS))
    with open("polygons.dat", "wb") as f:
        h.write(f)
        for polygon in POLYGONS:
            sz = struct.calcsize("<dd") * len(polygon)
            f.write(struct.pack("<i", struct.calcsize("<i") + sz))
            for p in polygon:
                f.write(struct.pack("<dd", *p))


if __name__ == "__main__":
    if not os.path.exists("polygons.dat"):
        write_polygons()
    with open("polygons.dat", "rb") as f:
        h = Header.from_file(f)
        polygons = []
        for _ in range(h.len):
            fmt_i = struct.Struct("<i")
            sz = struct.unpack("<i", f.read(struct.calcsize("<i")))[0]
            polygon = []
            for _ in range(sz // struct.calcsize("<dd")):
                polygon.append(struct.unpack("<dd", f.read(struct.calcsize("<dd"))))
            polygons.append(polygon)
        print(polygons)
