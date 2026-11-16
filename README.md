# Automata for Input Validation

**Course:** 21CSC301T Formal Language and Automata, CLA-2, Assessment Task 2
**Student:** Remiel Debora E (RA2411026050268), rd4822@srmist.edu.in
**Faculty:** Dr. C. Gunasundari, Assistant Professor, Department of AIML, SRM IST Tiruchirappalli

Three everyday form fields are checked here by finite automata that run on real strings:

| # | Field | Automaton | States (incl. trap) |
|---|---|---|---|
| 1 | Vehicle registration number (TN45AB1234) | shape DFA over {A, D, O}; value rule "real state code" | 12 → 29 |
| 2 | Indian mobile number (+91 / 91 / 0 / none) | NFA that guesses what a leading 9 means → subset DFA (already minimal) | 14 → 25 |
| 3 | Date DD/MM/YYYY | shape DFA → valid day for each month → leap years | 12 → 22 → 35 |

Every count comes from running the code (`python -m automata_validators.cli --stats`), and
every automaton is checked against an independent regex or integer arithmetic.

## Run it

Pure Python 3, no dependencies except `pytest` for the tests.

```bash
pip install pytest
python -m automata_validators.cli                          # accept/reject table for every field
python -m automata_validators.cli mobile 9198765432        # one string with its full δ-trace
python -m automata_validators.cli --stats                  # state counts of every design
python -m automata_validators.cli --limits                 # what each automaton cannot check
python -m pytest -q                                        # 15 checks
python tools/make_diagrams.py                              # rebuild diagrams + web demo (Graphviz)
```

**Browser demo:** open `docs/index.html` (or turn on GitHub Pages for `docs/`). Choose a field,
type, and watch the current state light up on the diagram.

## 1. Vehicle registration number

Format: state code (2 letters) + RTO number (2 digits) + series (1–2 letters) + 4 digits.
Σ = {A, D, O} (upper-case letter, digit, other).

![plate DFA](docs/diagrams/plate_dfa.png)

v5 is the only branching state: a second letter goes to v6, a digit starts the number. Any
other move goes to the trap. Requiring the first two letters to be one of the 36 real
state/UT codes needs the raw alphabet (A–Z, 0–9, other), because the machine must remember
the first letter; the minimal DFA grows from **12 to 29** states.

## 2. Indian mobile number

L = (+91 | 91 | 0 | ε) [6-9] [0-9]⁹. The digit classes are 0, 1, 9, 6–8, 2–5 and +, because 9
plays two roles. After a leading 9 the machine cannot know whether it started the country
code **91** or the number itself (`9198765432` is a valid 10-digit number, `919876543210` is
91 + a number). The NFA simply guesses:

![mobile NFA](docs/diagrams/mobile_nfa.png)

Subset construction keeps both guesses alive: after the first 9 the DFA is in {c2, n1}, and
from then on it runs **two counters two positions apart** ({n1,n3}, {n2,n4}, …, {n8,n10}).
The result has 24 live states plus the trap, and minimisation removes nothing, so the subset
DFA is already minimal.

![mobile DFA](docs/diagrams/mobile_dfa.png)

## 3. Date DD/MM/YYYY

| Rule | Alphabet | States (incl. trap) |
|---|---|---|
| Shape: 2 digits / 2 digits / 4 digits | {D, /, O} | 12 |
| Day valid for its month (29/02 always allowed) | {0–9, /, other} | 22 (minimal) |
| … and 29/02 only in leap years | {0–9, /, other} | 35 (minimal) |

Day/month validity is regular because only finitely many prefixes matter; minimisation folds
the 366 valid "DD/MM/" prefixes into 22 states (for example every valid day and month
ends in the same state t15). The leap-year rule is regular too: the DFA only needs
(first two digits of the year) mod 4 and the last two digits.

![date DFA with day-per-month rule](docs/diagrams/date_value_dfa.png)

## Tests

`tests/test_validators.py` has 15 checks, including: every class string up to length 11 for
the plate shape (265 720 strings); 40 000 plates with real and random state codes; all
1 398 101 strings up to length 10 over {+, 9, 1, 7} for the mobile NFA and DFA plus 60 000
random numbers; every calendar date of 2023–2026 and 29/02 of every year 1600–2400; all
10 000 DD/MM pairs with three years each; exact equivalence of the subset and minimal DFAs.

## What a finite automaton cannot do here

* Whether a vehicle is registered, a SIM is active or a date is in the past needs outside
  data (VAHAN, the operator, today's date).
* Value rules are regular but cost states: 12 → 29 for state codes, 12 → 35 for full dates.
  A lookup or a few lines of arithmetic beside the DFA is easier to maintain.
* "As many digits as letters" would not be regular at all (pumping lemma).

## Layout

```
automata_validators/automata.py    DFA, NFA, subset construction, product, minimisation, DOT export
automata_validators/validators.py  the three fields, test strings and limitations
automata_validators/cli.py         terminal demo
tests/test_validators.py           15 checks
tools/make_diagrams.py             builds docs/diagrams/*, docs/automata.json, docs/index.html
docs/                              diagrams and the browser demo
```
