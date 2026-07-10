#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os
from typing import (
    Iterable,
    Iterator,
    BinaryIO,
    Self,
    TYPE_CHECKING,
    ClassVar,
    Any,
    cast,
)
from itertools import chain
import struct

PointType = tuple[float, float]
PolygonType = list[PointType]
PolygonsType = list[PolygonType]
POLYGONS: PolygonsType = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 6.3), (1.2, 0.5), (4.6, 9.2)],
]
_I4DI = struct.Struct("<iddddi")
_INT = struct.Struct("<i")
_DD = struct.Struct("<dd")
HEADER_REF = (0x1234, 0.5, 0.5, 7.0, 9.2, 3)


# class StarIter:
#     def __iter__(self) -> Iterator[Any]:
#         for k, v in self.__dict__.items():
#             if isinstance(v, Iterable):
#                 yield from v
#             else:
#                 yield v


class SchemaInit:
    __schema__: ClassVar[tuple[str, ...]]

    def __init__(self, *args):
        t = list(args)
        for a in self.__schema__:
            setattr(self, a, t.pop(0))
        if t:
            raise TypeError(f"{args}: extra args")

    def __iter__(self) -> Iterator[Any]:
        for k, v in self.__dict__.items():
            if isinstance(v, Iterable):
                yield from v
            else:
                yield v

    def __repr__(self):
        args = ", ".join(f"{getattr(self, a)}" for a in self.__schema__)
        return f"{type(self).__name__}({args})"

    def __eq__(self, other: Any) -> bool:
        return (
            all((left == right) for left, right in zip(self, other))
            if isinstance(other, type(self))
            else False
        )


class Point(SchemaInit):
    x: ClassVar[float]
    y: ClassVar[float]
    __schema__ = ("x", "y")


class Bbox(SchemaInit):
    p1: ClassVar[Point]
    p2: ClassVar[Point]
    __schema__ = ("p1", "p2")


def get_bbox(poly: PolygonsType = POLYGONS) -> Bbox:
    p1 = Point(min(x for x, _ in chain(*poly)), min(y for _, y in chain(*poly)))
    p2 = Point(max(x for x, _ in chain(*poly)), max(y for _, y in chain(*poly)))
    return Bbox(p1, p2)


class Header(SchemaInit):
    count: ClassVar[int]
    __schema__ = ("magic", "x1", "y1", "x2", "y2", "count")

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        return cls(*_I4DI.unpack(f.read(_I4DI.size)))

    def write(self, f: BinaryIO) -> None:
        f.write(_I4DI.pack(*self))


def write_polygons() -> None:
    bb = get_bbox()
    if TYPE_CHECKING:
        h = Header(0x1234, bb.p1.x, bb.p1.y, bb.p2.x, bb.p2.y, len(POLYGONS))
    else:
        h = Header(*HEADER_REF)
    with open("polygons.dat", "wb") as f:
        h.write(f)
        for polygon in POLYGONS:
            sz = _DD.size * len(polygon)
            f.write(_INT.pack(_INT.size + sz))
            for p in polygon:
                f.write(_DD.pack(*p))


def read_polygons(f: BinaryIO) -> tuple[Header, PolygonsType]:
    h = Header.from_file(f)
    polygons: PolygonsType = []
    for _ in range(h.count):
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
        assert h == Header(*HEADER_REF)
        assert POLYGONS == polygons
