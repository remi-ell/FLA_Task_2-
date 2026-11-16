"""
15 checks for the Task 2 automata. Each automaton is compared with an
independently written rule or regular expression on every short string (or on
many random strings), so the diagrams are backed by evidence.
"""
import random
import re
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automata_validators.automata import all_strings, equivalent  # noqa: E402
from automata_validators.validators import (  # noqa: E402
    APPLICATIONS, DATE_LEAP_DFA, DATE_SHAPE_DFA, DATE_VALUE_DFA, MOBILE_DFA, MOBILE_NFA,
    MOBILE_REGEX, MOBILE_SUBSET, PLATE_DFA, PLATE_STATE_DFA, STATE_CODES, date_reference)

PLATE_REGEX = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}")


def test_listed_examples():                                           # 1
    for key, app in APPLICATIONS.items():
        assert len(app["accept"]) >= 5 and len(app["reject"]) >= 5, key
        for s in app["accept"]:
            assert app["dfa"].accepts(s), (key, s)
        for s in app["reject"]:
            assert not app["dfa"].accepts(s), (key, s)


def test_plate_shape_exhaustive_short():                              # 2
    """All 19 531 strings up to length 6 over {T, 4, a, -, B}: none may be accepted."""
    count = 0
    for s in all_strings("T4a-B", 6):
        count += 1
        assert PLATE_DFA.accepts(s) == bool(PLATE_REGEX.fullmatch(s)), s
    assert count == 19531


def test_plate_shape_class_strings():                                 # 3
    """Every class string up to length 11 over {A, D, O}: 265 720 strings."""
    count = 0
    for s in all_strings("AD-", 11):
        count += 1
        word = s.replace("A", "K").replace("D", "7")
        assert PLATE_DFA.accepts(word) == bool(PLATE_REGEX.fullmatch(word)), word
    assert count == 265720


def test_plate_state_codes_random():                                  # 4
    rnd = random.Random(268)
    letters = string.ascii_uppercase
    for _ in range(40000):
        code = rnd.choice(letters) + rnd.choice(letters) if rnd.random() < 0.5 \
            else rnd.choice(STATE_CODES)
        tail = f"{rnd.randint(0, 99):02d}" + "".join(rnd.choice(letters) for _ in range(rnd.randint(1, 2))) \
            + f"{rnd.randint(0, 9999):04d}"
        s = code + tail if rnd.random() < 0.9 else code + tail[:-1]
        expected = bool(PLATE_REGEX.fullmatch(s)) and s[:2] in STATE_CODES
        assert PLATE_STATE_DFA.accepts(s) == expected, s


def test_mobile_exhaustive_class_strings():                           # 5
    """All 1 398 101 strings up to length 10 over {+, 9, 1, 7}: covers every prefix case."""
    rx = re.compile(MOBILE_REGEX)
    count = 0
    for s in all_strings("+917", 10):
        count += 1
        expected = rx.fullmatch(s) is not None
        assert MOBILE_DFA.accepts(s) == expected, s
        assert MOBILE_NFA.accepts(s) == expected, s
    assert count == 1398101


def test_mobile_random_long_strings():                                # 6
    rx = re.compile(MOBILE_REGEX)
    rnd = random.Random(4822)
    pool = "+0123456789 "
    for _ in range(60000):
        prefix = rnd.choice(["", "+91", "91", "0", "+9", "00", "9"])
        s = prefix + "".join(rnd.choice(pool) for _ in range(rnd.randint(8, 11)))
        assert MOBILE_DFA.accepts(s) == (rx.fullmatch(s) is not None), s


def test_mobile_subset_and_minimal_equivalent():                      # 7
    same, counterexample = equivalent(MOBILE_SUBSET, MOBILE_DFA)
    assert same, counterexample
    assert MOBILE_DFA.size() == MOBILE_SUBSET.size()       # subset DFA is already minimal


def test_mobile_guess_on_nine():                                      # 8
    """'9198765432' (a number) and '919876543210' (91 + number) are both valid."""
    assert MOBILE_DFA.accepts("9198765432") and MOBILE_DFA.accepts("919876543210")
    ok, steps = MOBILE_DFA.run("9")
    assert steps[0][3] in MOBILE_DFA.members and MOBILE_DFA.members[steps[0][3]] == ["{c2,n1}"]


def test_date_every_day_of_four_years():                              # 9
    """All 1 461 real calendar dates of 2023-2026 plus 29/02 of every year 1600-2400."""
    import datetime
    day = datetime.date(2023, 1, 1)
    while day.year < 2027:
        s = day.strftime("%d/%m/%Y")
        assert DATE_LEAP_DFA.accepts(s) and DATE_VALUE_DFA.accepts(s), s
        day += datetime.timedelta(days=1)
    for y in range(1600, 2401):
        s = f"29/02/{y:04d}"
        leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
        assert DATE_LEAP_DFA.accepts(s) == leap, s


def test_date_all_ddmm_combinations():                                # 10
    """All 10 000 DD/MM pairs with three years each against integer arithmetic."""
    for d in range(100):
        for m in range(100):
            for y in ("2024", "2026", "1900"):
                s = f"{d:02d}/{m:02d}/{y}"
                assert DATE_VALUE_DFA.accepts(s) == date_reference(s, False), s
                assert DATE_LEAP_DFA.accepts(s) == date_reference(s, True), s


def test_date_random_strings():                                       # 11
    rnd = random.Random(16)
    pool = "0123/9"
    for _ in range(60000):
        s = "".join(rnd.choice(pool) for _ in range(rnd.randint(8, 11)))
        assert DATE_SHAPE_DFA.accepts(s) == bool(re.fullmatch(r"\d\d/\d\d/\d{4}", s)), s
        assert DATE_LEAP_DFA.accepts(s) == date_reference(s, True), s


def test_state_counts_match_report():                                 # 12
    assert (PLATE_DFA.size(), PLATE_STATE_DFA.size()) == (12, 29)
    assert (len(MOBILE_NFA.states), MOBILE_SUBSET.size(), MOBILE_DFA.size()) == (14, 25, 25)
    assert (DATE_SHAPE_DFA.size(), DATE_VALUE_DFA.size(), DATE_LEAP_DFA.size()) == (12, 22, 35)


def test_value_rules_refine_shape():                                  # 13
    """Every string accepted by a value DFA is also accepted by its shape DFA."""
    rnd = random.Random(5)
    for _ in range(20000):
        s = f"{rnd.randint(0, 39):02d}/{rnd.randint(0, 19):02d}/{rnd.randint(0, 9999):04d}"
        if DATE_LEAP_DFA.accepts(s):
            assert DATE_VALUE_DFA.accepts(s) and DATE_SHAPE_DFA.accepts(s)


def test_invalid_characters_go_to_trap():                             # 14
    assert not PLATE_DFA.accepts("TN45AB12З4")
    assert not MOBILE_DFA.accepts("98765-43210")
    assert not DATE_LEAP_DFA.accepts("16.11.2026")


def test_minimal_dfas_are_really_minimal():                           # 15
    for dfa in (PLATE_STATE_DFA, MOBILE_DFA, DATE_VALUE_DFA, DATE_LEAP_DFA):
        assert dfa.minimise().size() == dfa.size()
