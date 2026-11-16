"""Pure data: what goes where, and every constraint the user has ever stated.

No I/O. No ffmpeg. No file reads. Every build script in the project imports this
module, so there is exactly one copy of the truth and validate() runs on every build.

Adding a constraint here is how a constraint stops evaporating. A rule that lives only
in a conversation or a style note is gone by the next working session; a rule that lives
in validate() fails the build whether or not anyone remembered it.

Fill the CONSTRAINTS block before generating an assignment, not after the user has
listened to all of it. See README.md.
"""

# ---------------------------------------------------------------------------
# 1. COUNT.  Fill these first and say the ratio out loud to the user.
# ---------------------------------------------------------------------------

SOURCES: list[str] = []          # ids of the material available
TARGETS: list[str] = []          # ids of the slots to fill


def ratio() -> float:
    """Targets per source. This one number is what makes the right questions obvious:
    at 14:1 nothing survives being placed wherever it happens to score best."""
    return len(TARGETS) / len(SOURCES) if SOURCES else 0.0


# ---------------------------------------------------------------------------
# 2. CONSTRAINTS.  Written BEFORE generating, and shown to the user for confirmation.
#    If they cannot be filled in, that is the question to ask.
# ---------------------------------------------------------------------------

GOOD: list[str] = [
    # Prose, for the user to confirm. What makes an assignment good here?
    # e.g. "a replacement may run shorter than what it replaces, never longer"
]

FORBIDDEN: list[str] = [
    # Prose, for the user to confirm. What is never acceptable?
    # e.g. "no clip with recognisable speech on a creature sound"
]

BUDGETS: dict[str, int] = {
    # source id -> max placements across the whole project.
    # For material too recognisable to hear often.
}

NEVER_IN: dict[str, list[str]] = {
    # role/category -> source ids barred from it entirely.
}

RAPID: set[str] = set()
"""Targets (or groups) that fire many times in quick succession. Two of these must
never draw the same source: a repeat is most audible exactly where it repeats
fastest."""

MAX_CHAIN = 1
"""How many pieces of source material may be concatenated into one target. Every join
is a seam, and a seam is what makes a replacement sound assembled rather than uttered.
Raise this only after the user has said the seams are acceptable."""

MAX_SHARE = 0.15
"""No single source may take more than this fraction of all placements. Guards against
one clip quietly ending up everywhere while a third of the library sits idle."""


# ---------------------------------------------------------------------------
# 3. THE ASSIGNMENT.  Generated, corrected by the user, then kept here.
# ---------------------------------------------------------------------------

ASSIGNMENT: dict[str, list[str]] = {}   # target id -> [source ids], in play order

ROLE_OF: dict[str, str] = {}            # target id -> role/category, for NEVER_IN

GROUP_OF: dict[str, str] = {}           # target id -> group, for RAPID


# ---------------------------------------------------------------------------
# 4. VALIDATION.  Called by verify.py and by every build script.
# ---------------------------------------------------------------------------

def validate(assignment=None) -> list[str]:
    """Return a list of problems. Empty means the assignment satisfies every constraint
    the user has ever stated. It returns a list rather than raising on the first fault,
    so one build round trip reports every violation instead of the earliest one."""
    a = ASSIGNMENT if assignment is None else assignment
    problems: list[str] = []

    # -- the skeleton itself ------------------------------------------------
    if not SOURCES:
        problems.append("SOURCES is empty: step 1 of README.md has not been done")
    if not TARGETS:
        problems.append("TARGETS is empty: step 1 of README.md has not been done")
    if not GOOD and not FORBIDDEN:
        problems.append(
            "GOOD and FORBIDDEN are both empty: the constraint list was never written, "
            "so nothing below can be checked. Write it and confirm it with the user "
            "BEFORE generating (README.md step 2)")
    if not a:
        problems.append("ASSIGNMENT is empty: nothing to check yet")
    if problems:
        return problems

    known_sources, known_targets = set(SOURCES), set(TARGETS)

    # -- coverage and references -------------------------------------------
    missing = known_targets - set(a)
    if missing:
        shown = ", ".join(sorted(missing)[:8])
        more = " ..." if len(missing) > 8 else ""
        problems.append(
            f"{len(missing)} target(s) unassigned; they will silently fall back to the "
            f"original: {shown}{more}")
    for t in sorted(set(a) - known_targets):
        problems.append(f"assignment references unknown target: {t}")
    for t, srcs in sorted(a.items()):
        for s in srcs:
            if s not in known_sources:
                problems.append(f"target {t} references unknown source: {s}")

    # -- chain length -------------------------------------------------------
    for t, srcs in sorted(a.items()):
        if len(srcs) > MAX_CHAIN:
            problems.append(
                f"target {t} chains {len(srcs)} pieces, MAX_CHAIN is {MAX_CHAIN}")

    # -- per-source budgets -------------------------------------------------
    uses: dict[str, int] = {}
    for srcs in a.values():
        for s in srcs:
            uses[s] = uses.get(s, 0) + 1
    for s, cap in sorted(BUDGETS.items()):
        n = uses.get(s, 0)
        if n > cap:
            problems.append(f"source {s} used {n} times, budget is {cap}")

    # -- material barred from a role ---------------------------------------
    for t, srcs in sorted(a.items()):
        role = ROLE_OF.get(t, "")
        barred = NEVER_IN.get(role, ())
        for s in srcs:
            if s in barred:
                problems.append(
                    f"target {t} (role {role}) uses {s}, which is barred from that role")

    # -- repetition where it is most audible -------------------------------
    by_group: dict[str, list[str]] = {}
    for t in a:
        g = GROUP_OF.get(t)
        if g:
            by_group.setdefault(g, []).append(t)
    for g, members in sorted(by_group.items()):
        if len(members) < 2:
            continue
        if g not in RAPID and not any(t in RAPID for t in members):
            continue
        seen: dict[str, str] = {}
        for t in sorted(members):
            for s in a[t]:
                if s in seen:
                    problems.append(
                        f"rapid group {g}: {t} and {seen[s]} both use {s}; "
                        f"the repeat is audible exactly where it fires fastest")
                seen[s] = t

    # -- reuse spread -------------------------------------------------------
    total = sum(uses.values())
    if total:
        for s, n in sorted(uses.items(), key=lambda kv: -kv[1]):
            if n / total > MAX_SHARE:
                problems.append(
                    f"source {s} takes {n}/{total} placements ({n / total:.0%}), "
                    f"MAX_SHARE is {MAX_SHARE:.0%}")
            else:
                break
        idle = sorted(set(SOURCES) - set(uses))
        if idle:
            shown = ", ".join(idle[:8])
            more = " ..." if len(idle) > 8 else ""
            problems.append(
                f"{len(idle)} source(s) never used while others repeat: {shown}{more}")

    return problems


def summary() -> str:
    uses: dict[str, int] = {}
    for srcs in ASSIGNMENT.values():
        for s in srcs:
            uses[s] = uses.get(s, 0) + 1
    top = sorted(uses.items(), key=lambda kv: -kv[1])[:3]
    heaviest = ", heaviest: " + ", ".join(f"{s} x{n}" for s, n in top) if top else ""
    return (f"{len(SOURCES)} sources -> {len(TARGETS)} targets ({ratio():.1f}:1), "
            f"{len(ASSIGNMENT)} assigned, {len(uses)} sources in play{heaviest}")


if __name__ == "__main__":
    for p in validate():
        print("FAIL", p)
