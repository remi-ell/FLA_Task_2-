"""
The three Task 2 applications, each a finite automaton over character classes.

  1. Vehicle registration number  - shape DFA, plus the 'real state code' value rule
  2. Indian mobile number         - NFA that guesses whether a leading 9 starts the
                                    "91" country code or the number itself ->
                                    subset construction -> minimal DFA
  3. Date DD/MM/YYYY              - shape DFA, day-per-month rule, leap-year rule

An automaton only checks that a string is well-formed. Whether the vehicle is
registered, the SIM is active or the date lies in the past needs outside data.
"""
import string

from .automata import DFA, NFA

# ===========================================================================
# 1. Vehicle registration number, e.g. TN45AB1234 or KA01M7777
# ===========================================================================
# state code (2 letters) + RTO number (2 digits) + series (1-2 letters) + 4 digits
# Sigma = {A, D, O}: A = upper-case letter, D = digit, O = anything else.


def plate_class(ch):
    if ch in string.ascii_uppercase:
        return "A"
    if ch in string.digits:
        return "D"
    return "O"


PLATE_DFA = DFA(
    "Vehicle number (shape)", ["A", "D", "O"],
    {("v0", "A"): "v1", ("v1", "A"): "v2",                    # state code
     ("v2", "D"): "v3", ("v3", "D"): "v4",                    # RTO number
     ("v4", "A"): "v5", ("v5", "A"): "v6",                    # series: 1 or 2 letters
     ("v5", "D"): "n1", ("v6", "D"): "n1",                    # registration number
     ("n1", "D"): "n2", ("n2", "D"): "n3", ("n3", "D"): "n4"},
    "v0", {"n4"}, plate_class,
    states=["v0", "v1", "v2", "v3", "v4", "v5", "v6", "n1", "n2", "n3", "n4"])

STATE_CODES = ["AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "GA", "GJ", "HP",
               "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ",
               "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"]
RAW_PLATE_ALPHA = list(string.ascii_uppercase) + list(string.digits) + ["other"]


def raw_plate_class(ch):
    return ch if ch in string.ascii_uppercase + string.digits else "other"


def _plate_with_state_codes():
    """Same shape, but the first two letters must be a real state/UT code.
    Needs the raw alphabet: the machine must remember the first letter."""
    U, D = string.ascii_uppercase, string.digits
    delta = {}
    firsts = sorted({c[0] for c in STATE_CODES})
    for f in firsts:
        delta[("s", f)] = f"first_{f}"
    for code in STATE_CODES:
        delta[(f"first_{code[0]}", code[1])] = "v2"
    for d in D:
        delta[("v2", d)] = "v3"
        delta[("v3", d)] = "v4"
        delta[("v5", d)] = "n1"
        delta[("v6", d)] = "n1"
        delta[("n1", d)] = "n2"
        delta[("n2", d)] = "n3"
        delta[("n3", d)] = "n4"
    for u in U:
        delta[("v4", u)] = "v5"
        delta[("v5", u)] = "v6"
    raw = DFA("Vehicle number with real state code", RAW_PLATE_ALPHA, delta, "s", {"n4"},
              raw_plate_class)
    return raw.minimise("Vehicle number with real state code (minimal)", prefix="r")


PLATE_STATE_DFA = _plate_with_state_codes()

# ===========================================================================
# 2. Indian mobile number: optional +91 / 91 / 0 prefix, then 10 digits
#    starting with 6, 7, 8 or 9.
# ===========================================================================
# Sigma = {PLUS, ZERO, ONE, NINE, HI, MID, O}
#   HI = 6, 7, 8   MID = 2, 3, 4, 5   (9 has its own class because it can start
#   either the country code 91 or the number itself)
MOB_ALPHA = ["PLUS", "ZERO", "ONE", "NINE", "HI", "MID", "O"]
MOB_EDGE = {"PLUS": "+", "ZERO": "0", "ONE": "1", "NINE": "9", "HI": "6-8", "MID": "2-5"}
ANY_DIGIT = ["ZERO", "ONE", "NINE", "HI", "MID"]
LEADING = ["NINE", "HI"]                     # 6, 7, 8, 9


def mobile_class(ch):
    if ch == "+":
        return "PLUS"
    if ch == "0":
        return "ZERO"
    if ch == "1":
        return "ONE"
    if ch == "9":
        return "NINE"
    if ch in "678":
        return "HI"
    if ch in "2345":
        return "MID"
    return "O"


def _mobile_nfa():
    d = {}

    def arc(p, symbols, q):
        for s in symbols:
            d.setdefault((p, s), set()).add(q)
    arc("s", ["PLUS"], "c1")          # +91 ...
    arc("c1", ["NINE"], "c2")
    arc("s", ["NINE"], "c2")          # 91 ... (guess: the 9 starts the country code)
    arc("c2", ["ONE"], "n0")
    arc("s", ["ZERO"], "n0")          # 0 ... (trunk prefix)
    arc("s", LEADING, "n1")           # no prefix (guess: the 9 starts the number)
    arc("n0", LEADING, "n1")
    for k in range(1, 10):
        arc(f"n{k}", ANY_DIGIT, f"n{k + 1}")
    return NFA("Mobile number (NFA)", MOB_ALPHA, d, "s", {"n10"}, mobile_class)


MOBILE_NFA = _mobile_nfa()
MOBILE_SUBSET = MOBILE_NFA.subset_construction("Mobile number (subset DFA)")
MOBILE_DFA = MOBILE_SUBSET.minimise("Mobile number (minimal DFA)", prefix="m")

MOBILE_REGEX = r"(\+91|91|0)?[6-9][0-9]{9}"

# ===========================================================================
# 3. Date DD/MM/YYYY
# ===========================================================================
DATE_ALPHA_SHAPE = ["D", "SL", "O"]


def date_shape_class(ch):
    if ch in string.digits:
        return "D"
    return "SL" if ch == "/" else "O"


DATE_SHAPE_DFA = DFA(
    "Date (shape DD/MM/YYYY)", DATE_ALPHA_SHAPE,
    {("d0", "D"): "d1", ("d1", "D"): "d2", ("d2", "SL"): "d3",
     ("d3", "D"): "d4", ("d4", "D"): "d5", ("d5", "SL"): "d6",
     ("d6", "D"): "d7", ("d7", "D"): "d8", ("d8", "D"): "d9", ("d9", "D"): "d10"},
    "d0", {"d10"}, date_shape_class,
    states=[f"d{k}" for k in range(11)])

RAW_DATE_ALPHA = list(string.digits) + ["/", "other"]
DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def raw_date_class(ch):
    return ch if ch in string.digits + "/" else "other"


def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _date_dfa(leap_rule):
    """A trie over every valid 'DD/MM/' prefix (366 of them), followed by a year
    part. Without the leap rule any 4 digits follow; with it, 29/02 continues into
    a small machine that tracks just enough of the year to decide leap-ness:
    (first two digits) mod 4, then the last two digits. Minimisation then merges
    every state that needs to remember the same thing."""
    delta = {}
    valid = [f"{d:02d}/{m:02d}/" for m in range(1, 13)
             for d in range(1, DAYS_IN_MONTH[m - 1] + 1)]
    for p in valid:
        for k in range(len(p)):
            delta[(f"t:{p[:k]}", p[k])] = f"t:{p[:k + 1]}"
        feb29 = leap_rule and p == "29/02/"
        delta[(f"t:{p[:5]}", "/")] = "f29:0" if feb29 else "y:0"
    for k in range(4):
        for d in string.digits:
            delta[(f"y:{k}", d)] = f"y:{k + 1}"
    if leap_rule:
        for a in string.digits:
            delta[("f29:0", a)] = f"f29:1:{a}"
            for b in string.digits:
                delta[(f"f29:1:{a}", b)] = f"f29:2:{int(a + b) % 4}"
        for c in range(4):
            for e in string.digits:
                delta[(f"f29:2:{c}", e)] = f"f29:3:{c}:{e}"
                for f in string.digits:
                    yy = int(e + f)
                    leap = (yy % 4 == 0 and yy != 0) or (yy == 0 and c == 0)
                    delta[(f"f29:3:{c}:{e}", f)] = "y:4" if leap else "bad"
    name = "Date with leap-year rule" if leap_rule else "Date with day-per-month rule"
    raw = DFA(name, RAW_DATE_ALPHA, delta, "t:", {"y:4"}, raw_date_class)
    return raw.minimise(name + " (minimal)", prefix="t")


DATE_VALUE_DFA = _date_dfa(leap_rule=False)
DATE_LEAP_DFA = _date_dfa(leap_rule=True)


def date_reference(s, leap_rule):
    """Independent check with plain integer arithmetic."""
    if len(s) != 10 or s[2] != "/" or s[5] != "/":
        return False
    dd, mm, yy = s[:2], s[3:5], s[6:]
    if not (dd + mm + yy).isdigit():
        return False
    d, m, y = int(dd), int(mm), int(yy)
    if not 1 <= m <= 12 or not 1 <= d <= DAYS_IN_MONTH[m - 1]:
        return False
    if leap_rule and d == 29 and m == 2 and not is_leap(y):
        return False
    return True


# ===========================================================================
# Registry used by the CLI, the tests and the browser demo
# ===========================================================================
APPLICATIONS = {
    "plate": {
        "title": "Vehicle registration number",
        "dfa": PLATE_DFA,
        "accept": ["TN45AB1234", "KA01M7777", "DL01CA0420", "MH12DE1433", "TN09BZ0001",
                   "AP28CD5678"],
        "reject": ["TN45AB123", "TN-45-AB-1234", "tn45ab1234", "T45AB1234", "TN45ABC1234",
                   "TN451234", "TN45AB12345", ""],
    },
    "mobile": {
        "title": "Mobile number",
        "dfa": MOBILE_DFA,
        "accept": ["9876543210", "+919876543210", "919876543210", "09876543210",
                   "6300012345", "9198765432"],
        "reject": ["5876543210", "987654321", "+9198765432", "+09876543210",
                   "98765 43210", "0919876543210", "+91987654321"],
    },
    "date": {
        "title": "Date DD/MM/YYYY (with leap years)",
        "dfa": DATE_LEAP_DFA,
        "accept": ["16/11/2026", "01/01/2000", "29/02/2024", "29/02/2000", "31/12/1999",
                   "30/04/2025"],
        "reject": ["29/02/2026", "29/02/1900", "31/04/2025", "00/10/2026", "15/13/2026",
                   "1/11/2026", "16-11-2026", "16/11/26"],
    },
}

LIMITATIONS = {
    "plate": [
        "Only the shape is checked. Whether the vehicle is registered, or the plate is "
        "stolen, needs the VAHAN database - a lookup, not a language property.",
        f"Restricting the first two letters to the {len(STATE_CODES)} real state/UT codes "
        f"needs the raw alphabet and grows the DFA from {PLATE_DFA.size()} to "
        f"{PLATE_STATE_DFA.size()} states; a set lookup in code is simpler.",
    ],
    "mobile": [
        "The automaton cannot know whether the number is allotted or the SIM is active "
        "(needs the operator); it also cannot verify an OTP sent to it.",
        "Allowing any number of spaces between digit groups is still regular, but every "
        "position doubles; strip spaces before running the DFA.",
    ],
    "date": [
        "Days-per-month and leap years are regular because both depend on a bounded amount "
        "of the string, but they cost states: "
        f"{DATE_SHAPE_DFA.size()} (shape) -> {DATE_VALUE_DFA.size()} (day/month) -> "
        f"{DATE_LEAP_DFA.size()} (leap years).",
        "'The date is in the past' or 'age at least 18' depends on today's date, which "
        "is outside data - an ordinary comparison after parsing.",
    ],
}
