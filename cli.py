"""
Command-line demo for the Task 2 validators.

  python -m automata_validators.cli                        accept/reject table for every application
  python -m automata_validators.cli mobile 9198765432   one string with its full transition trace
  python -m automata_validators.cli --stats                state counts of every design
  python -m automata_validators.cli --limits               what each automaton cannot check
"""
import sys

from .automata import TRAP
from .validators import (APPLICATIONS, DATE_LEAP_DFA, DATE_SHAPE_DFA, DATE_VALUE_DFA,
                         LIMITATIONS, MOBILE_DFA, MOBILE_NFA, MOBILE_SUBSET, PLATE_DFA,
                         PLATE_STATE_DFA, STATE_CODES)

COLOUR = sys.stdout.isatty() or "--color" in sys.argv
GREEN, RED, BOLD, DIM, END = ("\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[0m") \
    if COLOUR else ("",) * 5


def shown(s):
    return "ε" if s == "" else (repr(s) if " " in s else s)


def verdict(ok):
    return f"{GREEN}ACCEPT{END}" if ok else f"{RED}REJECT{END}"


def table(key):
    app = APPLICATIONS[key]
    dfa = app["dfa"]
    print(f"\n{BOLD}{app['title']}{END}  {DIM}[{dfa.name}, {dfa.size()} states incl. trap]{END}")
    print(f"  {'input':<32}{'expected':<10}{'result':<8}  final state")
    rows = [(s, True) for s in app["accept"]] + [(s, False) for s in app["reject"]]
    good = 0
    for s, expected in rows:
        ok, steps = dfa.run(s)
        final = steps[-1][3] if steps else dfa.start
        good += ok == expected
        flag = "" if ok == expected else "   <-- MISMATCH"
        print(f"  {shown(s):<32}{('ACCEPT' if expected else 'REJECT'):<10}{verdict(ok)}  {final}{flag}")
    print(f"  {DIM}{good}/{len(rows)} as expected{END}")
    return good == len(rows)


def trace(key, text):
    dfa = APPLICATIONS[key]["dfa"]
    ok, steps = dfa.run(text)
    print(f"{BOLD}{dfa.name}{END} on '{text}'")
    for i, (p, ch, sym, q) in enumerate(steps, 1):
        note = "   (trap: can never accept)" if q == TRAP and p != TRAP else ""
        print(f"  {i:>2}. δ({p}, '{ch}' -> {sym}) = {q}{note}")
    final = steps[-1][3] if steps else dfa.start
    print(f"  final state {final} -> {'ACCEPTED' if ok else 'REJECTED'}")


def stats():
    print(f"{BOLD}Design comparison (reachable states, trap included){END}")
    rows = [
        ("Vehicle number: shape, Σ = {A, D, O}", PLATE_DFA.size()),
        (f"Vehicle number: real state code ({len(STATE_CODES)} codes), raw alphabet", PLATE_STATE_DFA.size()),
        ("Mobile number: hand-written NFA", len(MOBILE_NFA.states)),
        ("Mobile number: subset-construction DFA", MOBILE_SUBSET.size()),
        ("Mobile number: minimal DFA", MOBILE_DFA.size()),
        ("Date: shape DD/MM/YYYY, Σ = {D, /, O}", DATE_SHAPE_DFA.size()),
        ("Date: valid day for each month (minimal)", DATE_VALUE_DFA.size()),
        ("Date: plus leap years for 29/02 (minimal)", DATE_LEAP_DFA.size()),
    ]
    for name, n in rows:
        print(f"  {name:<62}{n:>5}")
    print(f"\n{BOLD}Minimal mobile DFA: which NFA subsets each state stands for{END}")
    for m, members in MOBILE_DFA.members.items():
        print(f"  {m:<6}{', '.join(members)}")


def limits():
    for key, items in LIMITATIONS.items():
        print(f"\n{BOLD}Limitations - {APPLICATIONS[key]['title']}{END}")
        for item in items:
            print(f"  - {item}")


def main(argv):
    args = [a for a in argv if a != "--color"]
    if not args:
        ok = all([table(k) for k in APPLICATIONS])
        print(f"\n{BOLD}All listed examples behaved as expected: {ok}{END}")
        return 0 if ok else 1
    if args[0] == "--stats":
        stats()
        return 0
    if args[0] == "--limits":
        limits()
        return 0
    if args[0] in APPLICATIONS and len(args) >= 2:
        trace(args[0], " ".join(args[1:]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
