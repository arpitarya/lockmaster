"""`lockmaster.toml` — SR-ARCHITECTURE decision 13.

    [main]
    branch = "main"                          # the branch lockmaster lands onto

    [checks]                                 # name = command; every one must pass
    tests = "python3 -m unittest discover -s tests"

    [generated]                              # path or glob = the command that rebuilds it
    "CHANGELOG.md" = "python3 scripts/changelog.py"

    [merge]                                  # path or glob = structural driver
    "work/WORKLOG.md" = "append-newest-first"

Read with `tomllib` on Python >= 3.11 and with the subset reader below on
3.9-3.10. Both feed the same validation, so a file means the same thing on
every Python: four tables of string values and nothing else. Anything outside
that subset is a loud error, never a guess (W-03 hazard).
"""
import re

DRIVERS = ("append-newest-first", "table-rows", "append")
TABLES = ("main", "checks", "generated", "merge")
FILENAME = "lockmaster.toml"


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, main="main", checks=None, generated=None, merge=None):
        self.main = main
        self.checks = dict(checks or {})
        self.generated = dict(generated or {})
        self.merge = dict(merge or {})

    def as_dict(self):
        return {"main": {"branch": self.main}, "checks": self.checks,
                "generated": self.generated, "merge": self.merge}


# ---------------------------------------------------------------- the subset reader

_BARE = re.compile(r"[A-Za-z0-9_-]+")
_ESCAPES = {"b": "\b", "t": "\t", "n": "\n", "f": "\f", "r": "\r", '"': '"', "\\": "\\"}


def _string(s, i, where):
    """Parse a basic ("...") or literal ('...') string at s[i]; return (value, next index)."""
    q = s[i]
    if s.startswith(q * 3, i):
        raise ConfigError(where + ": multi-line strings are outside lockmaster.toml's subset")
    i += 1
    buf = []
    while i < len(s):
        c = s[i]
        if c == q:
            return "".join(buf), i + 1
        if q == '"' and c == "\\":
            nxt = s[i + 1:i + 2]
            if nxt in _ESCAPES:
                buf.append(_ESCAPES[nxt])
                i += 2
                continue
            if nxt in ("u", "U"):
                n = 4 if nxt == "u" else 8
                hexs = s[i + 2:i + 2 + n]
                if not re.fullmatch(r"[0-9A-Fa-f]{%d}" % n, hexs):
                    raise ConfigError(where + ": bad \\" + nxt + " escape")
                buf.append(chr(int(hexs, 16)))
                i += 2 + n
                continue
            raise ConfigError(where + ": unknown escape \\" + nxt)
        buf.append(c)
        i += 1
    raise ConfigError(where + ": unterminated string")


def _rest_is_comment(s, i, where):
    rest = s[i:].strip()
    if rest and not rest.startswith("#"):
        raise ConfigError(where + ": unexpected `" + rest + "`")


def parse_subset(text):
    """The subset of TOML lockmaster.toml uses: `[table]` headers and
    `key = "string"` pairs, keys bare or quoted, comments. Returns nested dicts
    shaped like tomllib's result."""
    data, table = {}, None
    for n, raw in enumerate(text.splitlines(), 1):
        where = "lockmaster.toml line {}".format(n)
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            m = re.match(r"\[\s*([A-Za-z0-9_-]+)\s*\]", line)
            if not m or line.startswith("[["):
                raise ConfigError(where + ": only plain `[table]` headers are in the subset")
            _rest_is_comment(line, m.end(), where)
            name = m.group(1)
            if name in data:
                raise ConfigError(where + ": table [" + name + "] appears twice")
            table = data[name] = {}
            continue
        if table is None:
            raise ConfigError(where + ": a key outside any [table]")
        if line[0] in "\"'":
            key, i = _string(line, 0, where)
        else:
            m = _BARE.match(line)
            if not m:
                raise ConfigError(where + ": cannot read a key here")
            key, i = m.group(0), m.end()
        while i < len(line) and line[i] in " \t":
            i += 1
        if line[i:i + 1] == ".":
            raise ConfigError(where + ": dotted keys are outside the subset")
        if line[i:i + 1] != "=":
            raise ConfigError(where + ": expected `=` after the key")
        i += 1
        while i < len(line) and line[i] in " \t":
            i += 1
        if line[i:i + 1] not in ("\"", "'"):
            raise ConfigError(where + ": only string values are in the subset (got `" + line[i:] + "`)")
        value, i = _string(line, i, where)
        _rest_is_comment(line, i, where)
        if key in table:
            raise ConfigError(where + ": key `" + key + "` appears twice")
        table[key] = value
    return data


# ---------------------------------------------------------------- one validation

def parse(text):
    try:
        import tomllib  # Python >= 3.11
    except ImportError:
        data = parse_subset(text)
    else:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError("lockmaster.toml: " + str(e))
        # Valid TOML that 3.9 would refuse is refused here too: same file, same result.
        if parse_subset(text) != data:
            raise ConfigError("lockmaster.toml: uses TOML outside lockmaster's subset")
    return validate(data)


def validate(data):
    for name, table in data.items():
        if name not in TABLES:
            raise ConfigError("lockmaster.toml: unknown table [" + name + "]; the tables are "
                              + ", ".join("[" + t + "]" for t in TABLES))
        if not isinstance(table, dict):
            raise ConfigError("lockmaster.toml: `" + name + "` must be a [table]")
        for key, value in table.items():
            if not isinstance(value, str):
                raise ConfigError("lockmaster.toml: [{}] {} is not a string; only strings are in "
                                  "the subset".format(name, key))
    main = data.get("main", {})
    extra = set(main) - {"branch"}
    if extra:
        raise ConfigError("lockmaster.toml: [main] knows only `branch` (got " + ", ".join(sorted(extra)) + ")")
    merge = data.get("merge", {})
    for path, driver in merge.items():
        if driver not in DRIVERS:
            raise ConfigError("lockmaster.toml: [merge] {} = \"{}\" is no driver; the drivers are {}".format(
                path, driver, ", ".join(DRIVERS)))
    return Config(main.get("branch", "main"), data.get("checks"), data.get("generated"), merge)


def load(path):
    """The Config at `path`, or the defaults when there is no file."""
    try:
        with open(str(path), encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        return Config()
    return parse(text)
