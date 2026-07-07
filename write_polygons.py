#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from itertools import chain
from dataclasses import dataclass, field
import struct

POLYGONS = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 6.3), (1.2, 0.5), (4.6, 9.2)],
]


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Bbox:
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
class Header:
    magic: int
    x1: float
    y1: float
    x2: float
    y2: float
    len: int

    def write(self, f) -> None:
        f.write(
            # struct.pack("", self.__dict__.values())
            struct.pack(
                "<iddddi", self.magic, self.x1, self.y1, self.x2, self.y2, self.len
            )
        )

    def read(self, f) -> None:
        self.magic, self.x1, self.y1, self.x2, self.y2, self.len = f.read(
            struct.calcsize("<iddddi")
        )


def write_polygons() -> None:
    bb = get_bbox()
    # h = Header(0x1234, *bb, len(POLYGONS))
    h = Header(0x1234, bb.p1.x, bb.p1.y, bb.p2.x, bb.p2.y, len(POLYGONS))
    with open("polygons.dat", "wb") as f:
        h.write(f)


if __name__ == "__main__":
    write_polygons()
