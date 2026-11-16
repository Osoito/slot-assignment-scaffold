"""Layer 1: machine checks. No user, no ears, no game.

  python build/verify.py

Exits non-zero on any violation, so a broken assignment fails the build rather than
waiting to be noticed. Run it from every build script, not only by hand: a check that
only runs when someone remembers is the same as no check.

An unfilled scaffold fails on purpose. That is the point of it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mapping


def main() -> int:
    problems = mapping.validate()
    if problems:
        print(f"FAIL  {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  - {p}")
        print("\nFix these in mapping.py, then REGENERATE THE WHOLE SET.")
        print("Do not hand-patch only the items the user pointed at: they are")
        print("reporting a class of defect, not a list of them.")
        return 1

    print("OK   ", mapping.summary())
    if mapping.GOOD:
        print("\nGOOD:")
        for g in mapping.GOOD:
            print(f"  + {g}")
    if mapping.FORBIDDEN:
        print("\nFORBIDDEN:")
        for f in mapping.FORBIDDEN:
            print(f"  - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
