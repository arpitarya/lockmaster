"""The structural merge drivers — SR-ARCHITECTURE decision 10.

    append-newest-first   a worklog: both sides' new entries, the newer on top
    table-rows            a queue or table: both sides' new rows, a row both added kept once
    append                a lessons file: both sides' additions, in landing order

Git runs a driver as `merge.py <driver> %O %A %B %P` (ancestor, ours, theirs,
path) and reads the result from %A. When both sides only inserted lines at the
same place, the insertions are kept, one after the other. Every other overlap
goes to `git merge-file`, so a true conflict still conflicts: conflict markers
in %A and a non-zero exit. A driver never silently picks a side (W-03 hazard).

During a landing, "ours" is `main` and "theirs" is the change being landed, so
theirs is the newer side.

Standard library only, and importable without the rest of the package: git
calls this file directly.
"""
import difflib
import subprocess
import sys

DRIVERS = ("append-newest-first", "table-rows", "append")


def _hunks(base, side):
    sm = difflib.SequenceMatcher(None, base, side, autojunk=False)
    return [(i1, i2, side[j1:j2]) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def merge_lines(driver, base, ours, theirs):
    """The merged lines, or None when the two sides overlap in a way only a
    three-way text merge (and maybe a person) can settle."""
    if driver not in DRIVERS:
        raise ValueError("no such driver: " + driver)
    tagged = sorted([(h, "o") for h in _hunks(base, ours)] + [(h, "t") for h in _hunks(base, theirs)],
                    key=lambda x: (x[0][0], x[0][1]))
    # Group hunks whose base ranges touch or overlap (closed intervals, as diff3 does).
    groups = []
    for h, side in tagged:
        if groups and h[0] <= groups[-1]["end"]:
            groups[-1]["items"].append((h, side))
            groups[-1]["end"] = max(groups[-1]["end"], h[1])
        else:
            groups.append({"start": h[0], "end": h[1], "items": [(h, side)]})
    out, pos = [], 0
    for g in groups:
        items = g["items"]
        sides = {s for _, s in items}
        if len(sides) == 1:
            # One side only: apply its hunks in order.
            for (i1, i2, lines), _ in items:
                out += base[pos:i1] + lines
                pos = i2
            continue
        if len(items) != 2:
            return None
        (a1, a2, a), (b1, b2, b) = (h for h, _ in items)
        if (a1, a2, a) == (b1, b2, b):
            out += base[pos:a1] + a  # both made the same change
            pos = a2
            continue
        if not (a1 == a2 == b1 == b2):
            return None  # an edit or deletion overlapping the other side
        o = next(h for h, s in items if s == "o")[2]
        t = next(h for h, s in items if s == "t")[2]
        if driver == "table-rows":
            t = [l for l in t if l not in o]
        first, second = (t, o) if driver == "append-newest-first" else (o, t)
        out += base[pos:a1] + first + second
        pos = a1
    return out + base[pos:]


def _read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "surrogateescape").splitlines(True)


def main(argv):
    if len(argv) < 4 or argv[0] not in DRIVERS:
        print("usage: merge.py {" + "|".join(DRIVERS) + "} %O %A %B [%P]", file=sys.stderr)
        return 2
    driver, base_p, ours_p, theirs_p = argv[:4]
    label = argv[4] if len(argv) > 4 else ours_p
    merged = merge_lines(driver, _read(base_p), _read(ours_p), _read(theirs_p))
    if merged is not None:
        with open(ours_p, "wb") as fh:
            fh.write("".join(merged).encode("utf-8", "surrogateescape"))
        return 0
    # Not a pure insertion on both sides: git's own three-way merge decides,
    # and leaves conflict markers in %A when it cannot.
    r = subprocess.run(["git", "merge-file", "-L", label + " (main)", "-L", label + " (base)",
                        "-L", label + " (change)", ours_p, base_p, theirs_p])
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
