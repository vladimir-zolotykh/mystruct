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
    _I4DI = struct.Struct("<iddddi")
    magic: int = 0x1234
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    len: int = 0

    def __post_init__(self):
        bb = get_bbox()
        self.x1 = bb.p1.x
        self.y1 = bb.p1.y
        self.x2 = bb.p2.x
        self.y2 = bb.p2.y
        self.len = len(POLYGONS)

    def write(self, f: BinaryIO) -> None:
        f.write(self._I4DI.pack(*self))

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        return cls(*cls._I4DI.unpack(f.read(cls._I4DI.size)))


def write_polygons() -> None:
    bb = get_bbox()
    if TYPE_CHECKING:
        h = Header(0x1234, bb.p1.x, bb.p1.y, bb.p2.y, bb.p2.y, len(POLYGONS))
    else:
        h = Header()
    with open("polygons.dat", "wb") as f:
        h.write(f)
        _INT = struct.Struct("<i")
        _DD = struct.Struct("<dd")
        for polygon in POLYGONS:
            sz = _DD.size * len(polygon)
            f.write(_INT.pack(_INT.size + sz))
            for p in polygon:
                f.write(_DD.pack(*p))


def read_polygons(f: BinaryIO) -> tuple[Header, PolygonsType]:
    _INT = struct.Struct("<i")
    _DD = struct.Struct("<dd")
    h = Header.from_file(f)
    polygons: PolygonsType = []
    for _ in range(h.len):
        (sz,) = _INT.unpack(f.read(_INT.size))
        polygon: PolygonType = [
            _DD.unpack(f.read(_DD.size)) for _ in range(sz // _DD.size)
        ]
        polygons.append(polygon)
    return h, polygons


if __name__ == "__main__":
    if not os.path.exists("polygons.dat"):
        write_polygons()
    with open("polygons.dat", "rb") as f:
        h, polygons = read_polygons(f)
        assert h == Header()
        assert POLYGONS == polygons
