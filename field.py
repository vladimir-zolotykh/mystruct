#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import ClassVar, Iterator
import io
from functools import singledispatchmethod
import struct


class Field:
    def __init__(self, name: str, offset: int):
        self._name = name
        self.offset = offset

    def get_field(self, instance):
        raise NotImplementedError(f"{type(self)} must implement get_field")

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self.get_field(instance)


class FieldStr(Field):
    def __init__(self, name: str, fmt: str, offset: int):
        super().__init__(name, offset)
        self.fmt = fmt

    def get_field(self, instance):
        sl = slice(self.offset, self.offset + struct.calcsize(self.fmt))
        t = struct.unpack_from(self.fmt, instance.view[sl])
        return t[0] if len(t) == 1 else t


class FieldType(Field):
    def __init__(self, name: str, factory: "FieldMeta", offset: int):
        super().__init__(name, offset)
        self.factory = factory

    def get_field(self, instance):
        sl = slice(self.offset, self.offset + self.factory._view_size)
        return self.factory(instance.view[sl])


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict):
        off: int = 0
        fields = []
        for name, val in clsdict.items():
            if name[:2] == "__" and name[-2:] == "__":
                continue
            if isinstance(val, str):
                clsdict[name] = FieldStr(name, val, off)
                off += struct.calcsize(val)
            elif isinstance(val, FieldMeta):
                clsdict[name] = FieldType(name, val, off)
                off += val._view_size
            fields.append(name)
        clsdict["_view_size"] = off
        clsdict["_fields"] = fields
        return super().__new__(mcls, clsname, bases, clsdict)


class View(metaclass=FieldMeta):
    _fields: ClassVar[list[str]]
    _view_size: ClassVar[int]

    def __init__(self, bytesdata: bytes | memoryview):
        self.view = memoryview(bytesdata)

    def __repr__(self) -> str:
        args = ", ".join(f"{getattr(self, n)!r}" for n in self._fields)
        return f"{type(self).__name__}({args})"


class Point(View):
    x = "<d"
    y = "<d"


class Bbox(View):
    xy1 = Point
    xy2 = Point


class Header(View):
    magic = "<i"
    bbox = Bbox
    len = "<i"


class Polygon(View):
    _INT = struct.Struct("<i")

    @classmethod
    def from_file(cls, f):
        (sz,) = cls._INT.unpack_from(f.read(cls._INT.size))
        return cls(f.read(sz - cls._INT.size))

    @singledispatchmethod
    def iter_as(self, fmt_or_type):
        raise NotImplementedError("Must implement iter_as")

    @iter_as.register
    def _(self, fmt: str) -> Iterator[tuple[float, float]]:
        sz = struct.calcsize(fmt)
        for off in range(0, len(self.view), sz):
            sl = slice(off, off + sz)
            yield struct.unpack_from(fmt, self.view[sl])

    @iter_as.register
    def _(self, _type: FieldMeta) -> Iterator[FieldMeta]:
        sz = _type._view_size
        for off in range(0, len(self.view), sz):
            sl = slice(off, off + sz)
            yield _type(self.view[sl])


if __name__ == "__main__":
    with open("polygons.dat", "rb") as f:
        h = Header(f.read(Header._view_size))
        print(h)
        _DD = struct.Struct("<dd")
        data: bytes = f.read()
        f1: io.BytesIO = io.BytesIO(data)
        f2: io.BytesIO = io.BytesIO(data)

        for _ in range(h.len):
            polygon = Polygon.from_file(f1)
            for p in polygon.iter_as(_DD.format):
                print(p)
        for _ in range(h.len):
            polygon = Polygon.from_file(f2)
            for p in polygon.iter_as(Point):
                print(p)
