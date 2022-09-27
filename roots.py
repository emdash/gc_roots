#! /usr/bin/env python3
import inspect
import json
import os
import sys

from dataclasses import dataclass, field
from typing import Any, Dict, List

"""Quick-and-dirty visualizer for GC Roots"""

def escape(s): return s.replace("\"", "\\\"")
def quote(s):  return f"\"{escape(s)}\""

def fmt(addr, label, *fields):
    ports = (" | ").join(f"<{k}> {v}" for (k, v) in fields)
    output.print(f"{addr} [id={addr} label=\"{escape(label)} | {escape(ports)}\"];")

@dataclass
class HeapItem:
    pass

@dataclass
class Boxed:
    value: Any
    def render(self): fmt(id(self), "boxed", ("value", repr(self.value)))

@dataclass
class Slice:
    items: List[int]
    def render(self):
        fmt(id(self), "slice", *enumerate(range(len(self.items))))
        for (i, addr) in enumerate(self.items):
            output.print(f"{id(self)}:{i} -> {addr};")

@dataclass
class Scope:
    name: str
    items: list[int] = field(default_factory=list)
    def append(self, item): self.items.append(item)

    def render_items(self):
        scope = id(self)
        fmt(scope, f"scope:{self.name}", *enumerate(range(len(self.items))))

    def render_edges(self):
        scope = id(self)
        for (i, addr) in enumerate(self.items):
            if addr is not None:
                output.print(f"{scope}:{i} -> {addr};")

@dataclass
class Reservation:
    scope: Scope
    index: int


class FileSequence:

    def __init__(self, path, prefix=""):
        self.path = path
        self.prefix = prefix
        try:
            os.mkdir(self.path)
        except FileExistsError:
            pass
        self.cur = 0
        self.fileobj = None
        self.next()

    def next(self):
        path = os.path.join(self.path, f"{self.prefix}{self.cur}")
        self.fileobj = open(path, "w")
        self.cur += 1

    def print(self, *args):
        print(*args, file=self.fileobj)


class Heap:

    def __init__(self):
        self.items  = {}
        self.scopes = [Scope("__main__")]
        self.frame = 0
        self.render("__main__")

    def pushScope(self, name):
        self.scopes.append(Scope(name))
        self.render()

    def popScope(self):
        self.scopes.pop()
        self.render()

    def alloc(self, item):
        boxed = Boxed(item)
        addr = id(boxed)
        self.items[addr] = boxed
        self.render()
        return addr

    def addRoot(self, addr):
        self.scopes[-1].append(addr)
        self.render()
        return addr

    def reserve(self):
        top = self.scopes[-1]
        top.append(None)
        self.render()
        return Reservation(top, len(top.items) - 1)

    def claim(self, addr, res):
        res.scope.items[res.index] = add
        self.render()

    def render(self, label=None):
        if label is None:
            caller = inspect.currentframe().f_back.f_back
            lines, line = inspect.getsourcelines(caller)
            try:
                label = lines[caller.f_lineno - 1].strip()
            except BaseException:
                label = "not found"

        output.print("digraph {")

        # set some default style
        output.print(f"compound = true;")
        output.print(f"labeljust = \"l\";")
        output.print(f"labelloc = \"t\";")
        output.print(f"label = {quote(label)};")
        output.print("node [shape=record];")
        output.print("fontname=\"monospace\";")

        # create the stack
        output.print("subgraph cluster_stack {")
        output.print("label = stack; style=rounded; color=grey90")
        last = self.scopes[0]
        last.render_items()
        for scope in self.scopes[1:]:
            scope.render_items()
            output.print(f"{id(last)} -> {id(scope)};")
            last = scope
        output.print("}")

        # create the heap area
        output.print("subgraph cluster_heap {")
        output.print("label = heap; style=rounded; color=grey90; ")
        output.print("_ [style=invisible];")
        for item in self.items.values():
            item.render()
        output.print("}")

        # add the edges
        for scope in self.scopes:
            scope.render_edges()

        output.print("}")
        output.next()


if __name__ == "__main__":
    output = FileSequence("frames")
    path   = sys.argv[1]
    prog   = compile(open(path, "r").read(), path, "exec")
    gHeap  = Heap()
    exec(prog, {"gHeap": gHeap})
