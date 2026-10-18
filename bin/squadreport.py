"""squad-report collect: timeline, buckets, tokens, cost, config, partial states. Pure Python, read-only, no child process."""
from dataclasses import dataclass, field


class Unsupported(Exception):
    """Legacy flat squad (no scopes/ layout)."""


class Deadline(Exception):
    """`deadline` (a time.monotonic() value) passed."""


@dataclass
class Msg:
    ts: int
    frm: str
    to: str
    type: str      # first word of the text
    token: str     # first token after it
    text: str      # kept in memory only


@dataclass
class Escalation:
    id: str
    title: str
    raised_at: int
    answered_at: "int | None"


@dataclass
class Seg:
    start: int
    end: int
    bucket: str            # working|waiting|blocking|idle
    reason: "str | None"   # peer|po|human_input|None
    on: "str | None"       # agent name | "PO" | None
    stalled: bool = False  # additive: working gap longer than stall_s


@dataclass
class Turn:
    ts: int
    tokens: dict           # input, cache_read, cache_write, output
    cost: float
    model: str


@dataclass
class AgentTL:
    name: str
    role: str
    transcript_found: bool
    live: bool
    sessions: int
    segs: list = field(default_factory=list)
    turns: list = field(default_factory=list)
    cache_expiries: int = 0
    expiry_cost: float = 0.0   # additive: cost of the cache writes that followed an expiry


@dataclass
class Collected:
    scope_home: object
    squad: str
    name: str
    size: str
    window: tuple
    agents: dict
    msgs: list
    escalations: list
    roster: list
    cfg: dict
    sources: dict
    partial_reasons: list


def read_messages(path):
    raise NotImplementedError


def read_escalations(inbox_path):
    raise NotImplementedError


def load_config(plugin_root, squad_dir):
    raise NotImplementedError


def collect(scope_home, squad_dir, plugin_root, final=False, deadline=None):
    raise NotImplementedError


def base_data(c):
    raise NotImplementedError
