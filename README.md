# Asset pipeline scaffold

A four-file skeleton for any project that maps N pieces of material onto M slots. Audio clips onto sound effects, tracks onto music slots, images onto placements, copy variants onto positions.

It came out of two Binding of Isaac mods I shipped to the Steam Workshop, a [music mod](https://steamcommunity.com/sharedfiles/filedetails/?id=3787641648) at 16 masters over 85 slots and a [sound effect mod](https://steamcommunity.com/sharedfiles/filedetails/?id=3798883789) at 43 clips over the 590 slots it started from, 673 by release. Both went wrong in the same way before they went right. So the order of the steps below is the actual content of this repository. The code is small. The sequence is the part that was expensive to learn.

Copy `build/` into the project and work in this order.

## Running it

Python 3.11 or later, no dependencies.

```
python build/audition.py --demo   # see the shape of the decision surface
python build/verify.py            # non-zero on any violation. Call it from every build script.
python build/selftest.py          # proves each check actually fires
```

## 1. Count

Fill `SOURCES` and `TARGETS` in `mapping.py`, then say the ratio out loud to whoever the work is for.

43 clips over 590 slots is 14:1. That single number is what makes the right questions obvious. At 14:1 nothing survives being placed wherever it happens to score best, and "which material is too recognisable to hear often?" asks itself.

## 2. Write the constraint list, and confirm it

Fill `GOOD`, `FORBIDDEN`, `BUDGETS`, `NEVER_IN`, `RAPID`, `MAX_CHAIN` and `MAX_SHARE`, and show them to the person deciding **before generating anything**.

If they cannot be filled in, that is the question to ask. Asking costs one message. Not asking costs them reviewing the whole set and reporting the defects one at a time.

## 3. Ship the first decision surface

`render(rows, out)` in `audition.py` writes a self-contained HTML page with stable numbering, showing the original against its replacement, playable or viewable in place. Build this before any other pipeline work, and build only as much pipeline as the page needs.

**The numbers on that page are the interface.** Feedback comes back as "16 should sound angrier", "38, keep only short-18", "G1 needs replacing, try 3". Once a page has been handed over its numbers are frozen, because renumbering invalidates every instruction already given against it.

## 4. Sample before bulk

Generate a batch that spans the categories and hand that over first. A defect found at 20 items is one regeneration. The same defect found at 590 is a full review cycle thrown away.

## 5. Every stated constraint becomes a check

The moment a constraint is stated, add it to `mapping.validate()` **and** add a case to `selftest.py` that fails without it. Then regenerate the whole set.

Never hand-patch only the items that were pointed at. They are a report of a whole class of defect, and the rest of that class is still in there.

## Why the checks live in code

The rule "anything that must hold across many items belongs in code, because attention does not hold it" was written down twice as prose, in a general style guide and then in a handoff document aimed specifically at the next project. I broke it both times, the second time with that file open.

Prose does not hold. A `validate()` that every build script calls and a `verify.py` that exits non-zero do, because they work whether or not anyone remembered the rule.

The seven cases in `selftest.py` are the real defects that reached a listener before the corresponding check existed. Each was cheap to write. None was written until after someone complained.

## Layout

| File | What it is |
|---|---|
| `build/mapping.py` | Pure data, zero I/O. Sources, targets, constraints, the assignment, `validate()` |
| `build/verify.py` | Runs `validate()`, prints every problem, exits non-zero |
| `build/selftest.py` | Reintroduces each real defect, proves the check fires |
| `build/audition.py` | The decision surface. Stable numbers, original against replacement, playable in place |

## Notes

This is a scaffold, so `mapping.py` ships empty on purpose. `python build/verify.py` on a fresh copy exits non-zero and tells you step 1 has not been done yet.
