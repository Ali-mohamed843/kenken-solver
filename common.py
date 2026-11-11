from __future__ import annotations
import json, time
from pathlib import Path
from typing import Callable

SAMPLE_PUZZLES = {
    "4x4": {"n": 4, "cages": [
        {"op": "+", "target": 3, "cells": [(0,0),(0,1)]}, {"op": "-", "target": 1, "cells": [(0,2),(0,3)]},
        {"op": "-", "target": 1, "cells": [(1,0),(2,0)]}, {"op": "-", "target": 1, "cells": [(1,1),(1,2)]},
        {"op": "-", "target": 1, "cells": [(1,3),(2,3)]}, {"op": "-", "target": 1, "cells": [(2,1),(3,1)]},
        {"op": "-", "target": 1, "cells": [(2,2),(3,2)]}, {"op": "=", "target": 4, "cells": [(3,0)]},
        {"op": "=", "target": 3, "cells": [(3,3)]}]},
    "5x5": {"n": 5, "cages": [
        {"op": "=", "target": 1, "cells": [(0,0)]}, {"op": "=", "target": 2, "cells": [(0,1)]}, {"op": "=", "target": 3, "cells": [(0,2)]}, {"op": "=", "target": 4, "cells": [(0,3)]}, {"op": "=", "target": 5, "cells": [(0,4)]},
        {"op": "=", "target": 2, "cells": [(1,0)]}, {"op": "-", "target": 2, "cells": [(1,1),(1,2)]}, {"op": "-", "target": 1, "cells": [(1,3),(1,4)]},
        {"op": "=", "target": 3, "cells": [(2,0)]}, {"op": "-", "target": 2, "cells": [(2,1),(2,2)]}, {"op": "-", "target": 1, "cells": [(2,3),(2,4)]},
        {"op": "=", "target": 4, "cells": [(3,0)]}, {"op": "-", "target": 2, "cells": [(3,1),(3,2)]}, {"op": "-", "target": 1, "cells": [(3,3),(3,4)]},
        {"op": "=", "target": 5, "cells": [(4,0)]}, {"op": "-", "target": 2, "cells": [(4,1),(4,2)]}, {"op": "-", "target": 1, "cells": [(4,3),(4,4)]}]},
    "6x6": {"n": 6, "cages": [
        {"op": "=", "target": 1, "cells": [(0,0)]}, {"op": "=", "target": 2, "cells": [(0,1)]}, {"op": "=", "target": 3, "cells": [(0,2)]}, {"op": "=", "target": 4, "cells": [(0,3)]}, {"op": "=", "target": 5, "cells": [(0,4)]}, {"op": "=", "target": 6, "cells": [(0,5)]},
        {"op": "=", "target": 2, "cells": [(1,0)]}, {"op": "-", "target": 2, "cells": [(1,1),(1,2)]}, {"op": "-", "target": 1, "cells": [(1,3),(1,4)]}, {"op": "=", "target": 1, "cells": [(1,5)]},
        {"op": "=", "target": 3, "cells": [(2,0)]}, {"op": "-", "target": 2, "cells": [(2,1),(2,2)]}, {"op": "-", "target": 1, "cells": [(2,3),(2,4)]}, {"op": "=", "target": 2, "cells": [(2,5)]},
        {"op": "=", "target": 4, "cells": [(3,0)]}, {"op": "-", "target": 2, "cells": [(3,1),(3,2)]}, {"op": "-", "target": 1, "cells": [(3,3),(3,4)]}, {"op": "=", "target": 3, "cells": [(3,5)]},
        {"op": "=", "target": 5, "cells": [(4,0)]}, {"op": "-", "target": 2, "cells": [(4,1),(4,2)]}, {"op": "-", "target": 1, "cells": [(4,3),(4,4)]}, {"op": "=", "target": 4, "cells": [(4,5)]},
        {"op": "=", "target": 6, "cells": [(5,0)]}, {"op": "-", "target": 2, "cells": [(5,1),(5,2)]}, {"op": "-", "target": 1, "cells": [(5,3),(5,4)]}, {"op": "=", "target": 5, "cells": [(5,5)]}]}
}

def _make_sample(n):
    cages=[]
    for r in range(n):
        c=0
        while c<n:
            if c+1<n:
                a=(r+c)%n+1; b=(r+c+1)%n+1
                cages.append({"op":"+","target":a+b,"cells":[(r,c),(r,c+1)]}); c+=2
            else:
                cages.append({"op":"=","target":(r+c)%n+1,"cells":[(r,c)]}); c+=1
    return {"n":n,"cages":cages}

SAMPLE_PUZZLES={f"{n}x{n}":_make_sample(n) for n in (4,5,6)}

def normalize_puzzle(puzzle):
    p = dict(puzzle); p["n"] = int(p["n"])
    p["cages"] = [{**c, "cells": [tuple(map(int, x)) for x in c["cells"]]} for c in p["cages"]]
    validate_puzzle(p); return p

def validate_puzzle(puzzle):
    n = int(puzzle["n"])
    if not 3 <= n <= 9: raise ValueError("Grid size N must be from 3 through 9.")
    seen = set()
    for cage in puzzle["cages"]:
        if cage.get("op") not in {"+", "-", "*", "/", "="}: raise ValueError("Unsupported cage operation.")
        if not cage.get("cells"): raise ValueError("Every cage must contain at least one cell.")
        if cage["op"] == "=" and len(cage["cells"]) != 1: raise ValueError("An '=' cage must contain one cell.")
        for r,c in cage["cells"]:
            if not (0 <= r < n and 0 <= c < n): raise ValueError(f"Cell {(r,c)} is outside the grid.")
            if (r,c) in seen: raise ValueError(f"Cell {(r,c)} appears in more than one cage.")
            seen.add((r,c))
    if len(seen) != n*n: raise ValueError(f"Cages must cover all {n*n} cells (currently {len(seen)}).")

def empty_grid(n): return [[0 for _ in range(n)] for _ in range(n)]

def cage_ok(values, op, target):
    if not values or any(v == 0 for v in values): return True
    if op == "+": return sum(values) == target
    if op == "*":
        product = 1
        for v in values: product *= v
        return product == target
    if op == "-": return len(values) == 2 and abs(values[0]-values[1]) == target
    if op == "/":
        return len(values) == 2 and max(values) % min(values) == 0 and max(values)//min(values) == target
    return len(values) == 1 and values[0] == target

def _cage_possible(values, cage, n):
    vals = [v for v in values if v]
    missing = len(values)-len(vals); op, target = cage["op"], cage["target"]
    if not missing: return cage_ok(vals, op, target)
    if op == "=": return target in range(1,n+1)
    if op == "+": return sum(vals)+missing <= target <= sum(vals)+missing*n
    if op == "*":
        prod=1
        for v in vals: prod *= v
        return prod <= target and target % prod == 0 and prod*(n**missing) >= target
    if op in ("-", "/"): return missing == 1 and len(values) == 2
    return False

def fitness(grid, puzzle):
    p=normalize_puzzle(puzzle); n=p["n"]; score=0
    for row in grid: score += n-len(set(v for v in row if v))
    for c in range(n): score += n-len(set(grid[r][c] for r in range(n) if grid[r][c]))
    for cage in p["cages"]:
        vals=[grid[r][c] for r,c in cage["cells"]]
        if any(v == 0 for v in vals): score += sum(v == 0 for v in vals)+1
        elif not cage_ok(vals,cage["op"],cage["target"]): score += 1
    return score

def is_solved(grid, puzzle):
    p=normalize_puzzle(puzzle); n=p["n"]
    return len(grid)==n and all(len(row)==n and set(row)==set(range(1,n+1)) for row in grid) and all({grid[r][c] for r,c in cage["cells"]} and cage_ok([grid[r][c] for r,c in cage["cells"]],cage["op"],cage["target"]) for cage in p["cages"])

def load_puzzle(path):
    with open(path, encoding="utf-8") as f: return normalize_puzzle(json.load(f))

def save_puzzle(puzzle, path):
    p=normalize_puzzle(puzzle); p["cages"]=[{**c,"cells":[list(x) for x in c["cells"]]} for c in p["cages"]]
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(p,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def run_with_metrics(solve_fn: Callable, puzzle, **kwargs):
    start=time.perf_counter(); errors=[]
    try:
        result=solve_fn(puzzle,**kwargs); grid=result.get("grid",empty_grid(puzzle["n"]))
        solved=is_solved(grid,puzzle)
        return {"time":time.perf_counter()-start,"steps":result.get("steps",0),"errors":errors,"solved":solved,"grid":grid,"result":result}
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        return {"time":time.perf_counter()-start,"steps":0,"errors":errors,"solved":False,"grid":empty_grid(puzzle["n"]),"result":{}}


# --- Reference GUI puzzle model and text format ---
import random

OPS = {"+": "+", "-": "-", "*": "×", "/": "÷", "=": ""}


class Cage:
    def __init__(self, cells, op, target):
        self.cells = list(cells)          
        self.op = op                     
        self.target = target

    def ok(self, vals):
        t, op = self.target, self.op
        if op == "=":
            return vals[0] == t
        if op == "+":
            return sum(vals) == t
        if op == "*":
            p = 1
            for v in vals:
                p *= v
            return p == t
        a, b = max(vals), min(vals)
        if op == "-":
            return len(vals) == 2 and a - b == t
        if op == "/":
            return len(vals) == 2 and a % b == 0 and a // b == t
        return False

    def label(self):
        return f"{self.target}{OPS[self.op]}"


class Puzzle:
    def __init__(self, n, cages, solution=None):
        self.n = n
        self.cages = cages
        self.solution = solution          
        self.cage_of = [[-1] * n for _ in range(n)]
        for k, cg in enumerate(cages):
            for r, c in cg.cells:
                self.cage_of[r][c] = k

    def validate(self):
        n = self.n
        if any(self.cage_of[r][c] < 0 for r in range(n) for c in range(n)):
            return "Every cell must belong to a cage."
        for cg in self.cages:
            if cg.op in "-/" and len(cg.cells) != 2:
                return f"Cage {cg.label()} uses - or ÷, so it must have exactly 2 cells."
            if cg.op == "=" and len(cg.cells) != 1:
                return f"Cage {cg.label()} has no operation, so it must have 1 cell."
        return None

    def errors(self, g):
        """Return (number of violations, set of bad cells) for a full or partial grid."""
        n, bad, count = self.n, set(), 0
        for i in range(n):
            for line in ([(i, c) for c in range(n)], [(r, i) for r in range(n)]):
                seen = {}
                for cell in line:
                    v = g[cell[0]][cell[1]]
                    if v:
                        seen.setdefault(v, []).append(cell)
                for cells in seen.values():
                    if len(cells) > 1:
                        count += len(cells) - 1
                        bad.update(cells)
        for cg in self.cages:
            vals = [g[r][c] for r, c in cg.cells]
            if all(vals) and not cg.ok(vals):
                count += 1
                bad.update(cg.cells)
        return count, bad

    def is_solved(self, g):
        return all(all(row) for row in g) and self.errors(g)[0] == 0


def generate(n, seed=None):
    rnd = random.Random(seed)
    base = [[(r + c) % n + 1 for c in range(n)] for r in range(n)]   # Latin square
    rnd.shuffle(base)
    cols = list(range(n))
    rnd.shuffle(cols)
    sym = list(range(1, n + 1))
    rnd.shuffle(sym)
    sol = [[sym[base[r][c] - 1] for c in cols] for r in range(n)]

    free = {(r, c) for r in range(n) for c in range(n)}
    cages = []
    order = sorted(free)
    rnd.shuffle(order)
    for start in order:
        if start not in free:
            continue
        size = rnd.choices([1, 2, 3, 4], weights=[8, 50, 30, 12])[0]
        cells = [start]
        free.discard(start)
        while len(cells) < size:
            opts = [(r + dr, c + dc) for r, c in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (r + dr, c + dc) in free]
            if not opts:
                break
            nxt = rnd.choice(opts)
            cells.append(nxt)
            free.discard(nxt)
        vals = [sol[r][c] for r, c in cells]
        if len(cells) == 1:
            op, t = "=", vals[0]
        elif len(cells) == 2:
            a, b = max(vals), min(vals)
            choices = ["+", "-", "*"] + (["/", "/"] if a % b == 0 else [])
            op = rnd.choice(choices)
            t = {"+": a + b, "-": a - b, "*": a * b, "/": a // b if a % b == 0 else 0}[op]
        else:
            op = rnd.choice(["+", "*"])
            t = sum(vals)
            if op == "*":
                t = 1
                for v in vals:
                    t *= v
        cages.append(Cage(cells, op, t))
    return Puzzle(n, cages, sol)


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def to_text(p):
    lab = lambda k: LETTERS[k] if k < len(LETTERS) else f"c{k}"
    lines = ["# KenKen puzzle: size, then the cage map (one label per cell), then 'label target op'",
             str(p.n)]
    for r in range(p.n):
        lines.append(" ".join(lab(p.cage_of[r][c]) for c in range(p.n)))
    for k, cg in enumerate(p.cages):
        lines.append(f"{lab(k)} {cg.target}{cg.op if cg.op != '=' else ''}")
    return "\n".join(lines)


def from_text(text):
    lines = [ln.split("#")[0].strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    n = int(lines[0])
    if not 2 <= n <= 9:
        raise ValueError("Size must be 2..9")
    grid = []
    for ln in lines[1:n + 1]:
        toks = ln.split()
        if len(toks) == 1 and len(toks[0]) == n:
            toks = list(toks[0])
        if len(toks) != n:
            raise ValueError(f"Row '{ln}' must have {n} labels")
        grid.append(toks)
    rules = {}
    for ln in lines[n + 1:]:
        toks = ln.replace("x", "*").replace("×", "*").replace("÷", "/").split()
        lab, rest = toks[0], "".join(toks[1:])
        op = rest[-1] if rest and rest[-1] in "+-*/=" else "="
        num = rest[:-1] if rest and rest[-1] in "+-*/=" else rest
        rules[lab] = (op, int(num))
    groups = {}
    for r in range(n):
        for c in range(n):
            groups.setdefault(grid[r][c], []).append((r, c))
    cages = []
    for lab, cells in groups.items():
        if lab not in rules:
            raise ValueError(f"No rule given for cage '{lab}'")
        op, t = rules[lab]
        cages.append(Cage(cells, op, t))
    return Puzzle(n, cages)



class Stopped(Exception):
    pass


class Context:
    def __init__(self, emit, stop_event, time_limit):
        self.emit, self.stop_event = emit, stop_event
        self.t0 = time.time()
        self.deadline = self.t0 + time_limit
        self.reason = ""

    def check(self):
        if self.stop_event.is_set():
            self.reason = "stopped by user"
            raise Stopped
        if time.time() > self.deadline:
            self.reason = "time limit reached"
            raise Stopped

    def elapsed(self):
        return time.time() - self.t0


def result(algo, p, grid, ctx, work, note):
    grid = [row[:] for row in grid] if grid else None
    cost = p.errors(grid)[0] if grid else None
    solved = bool(grid) and p.is_solved(grid)
    return dict(algo=algo, grid=grid, solved=solved, cost=cost, time=ctx.elapsed(), work=work, note=note)
