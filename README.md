# Finite Automata for Real-Time Validation

**Course:** 21CSC301T Formal Language and Automata, CLA-2, Assessment Task 2
**Student:** Jaisri (RA2411026050248), B.Tech CSE (AIML), III Year / V Semester, Section AIML-D
**Faculty:** Dr. C. Gunasundari, Assistant Professor, Department of AIML, SRM IST Tiruchirappalli

Every login page, ATM keypad and sign-up form has to decide, within a keystroke,
whether the text it received is even *shaped* correctly. This repository builds
finite automata for three such checks and runs them on real strings:

| # | Application | Automaton | States (incl. trap) |
|---|---|---|---|
| 1 | ATM PIN and card lock | PIN DFA over {D, O} + card-lock DFA over events {C, W} | 6 and 4 |
| 2 | Password policy | 5 component DFAs → product DFA → minimal DFA | 22 → 192 → 81 |
| 3 | E-mail format | hand-written NFA → subset construction → minimal DFA | 9 → 9 + trap → 8 + trap |

Every state count above comes from running the code (`python -m fa_validators.cli --stats`),
and every automaton is checked against an independently written rule or regular
expression on thousands of generated strings.

## Run it

Pure Python 3, no dependencies except `pytest` for the tests.

```bash
pip install pytest                                  # only needed for the tests
python -m fa_validators.cli                         # accept/reject table for every application
python -m fa_validators.cli email jaisri@srm.c0m    # one string with its full δ-trace
python -m fa_validators.cli --stats                 # design comparison (state counts)
python -m fa_validators.cli --limits                # what each automaton cannot check
python -m pytest -q                                 # 14 checks
python tools/make_diagrams.py                       # rebuild diagrams + web demo (needs Graphviz)
```

**Browser demo:** open `docs/index.html` (or enable GitHub Pages on the `docs/` folder).
Pick an application and type a string. The page highlights the current state on the
diagram and lists every transition taken.

## Design idea: character classes and a trap state

To keep the diagrams readable, an automaton reads **character classes** rather than raw
characters (for example `D` for any digit, `U` for an upper-case letter). A one-line
classifier converts each typed character into its class. Anything outside the allowed
classes sends the machine to a dead (**trap**) state that never accepts. The trap is left
out of the drawings.

**Syntax versus semantics.** An automaton only answers "is this string well-formed?".
Whether 5309 is *this* customer's PIN, whether the mailbox exists, or whether a password
appears in a breach list are semantic questions. They need a bank record, a DNS/SMTP
lookup or a blocklist, and are handled by ordinary code after the automaton has accepted.

Assumptions: input is ASCII; a space or tab is never allowed inside a password; the
e-mail rule is the practical subset of RFC 5322 that web forms enforce.

## 1. ATM PIN and card lock

* Σ = {D, O} (digit, other) and L<sub>PIN</sub> = { w ∈ Σ* : w = D⁴ }, i.e. exactly four digits.
* States q0–q4 count the digits read, and only q4 accepts. A fifth digit, or any O, goes to the trap.

![PIN DFA](docs/diagrams/pin_dfa.png)

**Card lock.** A second DFA reads events, Σ = {C, W} (correct PIN, wrong PIN). States
w0, w1, w2 count consecutive wrong entries, a correct entry resets the count, and the
third consecutive W enters the absorbing state LOCKED. The accepting states are w0–w2
("card still usable"), so the language is the set of event strings with no substring `WWW`.

![Card-lock DFA](docs/diagrams/card_lock_dfa.png)

| PIN rule | Alphabet | States (incl. trap) | Comment |
|---|---|---|---|
| Exactly 4 digits | {D, O} | 6 | q0–q4 and trap |
| 4 or 6 digits | {D, O} | 8 | accepting at both q4 and q6 (`pin46_dfa.png`) |
| 4 digits, not all equal | {0,…,9, other} | 35 (minimal) | must remember the first digit; better done as a one-line check in code |

Shape rules cost very little. A *value* rule forces the raw digit alphabet, because the
machine must remember the first digit, and the minimal DFA grows from 6 to 35 states.

## 2. Password policy

**Policy:** 8 to 12 characters, at least one upper-case letter, one lower-case letter and
one digit, and no whitespace. Special characters are allowed but not required (NIST SP
800-63B advises against heavy composition rules).

* Σ = {U, L, D, S, W} (S = any other printable character, W = whitespace)
* L = L<sub>len</sub> ∩ L<sub>U</sub> ∩ L<sub>L</sub> ∩ L<sub>D</sub> ∩ L<sub>noW</sub>

Each part is a tiny DFA, and regular languages are closed under intersection, so the
product construction joins them into one machine.

| Length 8–12 (every class counts as `*`; l8–l12 accept, l13 is dead) |
|---|
| ![length](docs/diagrams/password_length.png) |

| "Contains an upper-case letter" (the L and D checks are identical) | "No whitespace" |
|---|---|
| ![upper](docs/diagrams/password_has_upper.png) | ![no ws](docs/diagrams/password_no_whitespace.png) |

| Design | States | Comment |
|---|---|---|
| 5 component DFAs side by side (14 + 2 + 2 + 2 + 2) | 22 | one rule = one machine; easiest to change |
| Product DFA, reachable part only | 192 | the single machine the theory promises (224 possible) |
| Product DFA after minimisation | 81 | 111 equivalent states merged; 80 live states plus one trap |

The reachable product is almost nine times the size of the five parts together, because
its state is the *combination* of length and flags. The single machine is useful for
proofs and hardware, but a real system would keep the five small checks, since changing
the policy then touches only one component.

## 3. E-mail format

```
local  = alnum+ ( [._+-] alnum+ )*
domain = ( label "." )+ tld          label = alnum+ ( "-"+ alnum+ )*
tld    = letter{2,}
```

Σ = {L, D, ".", "-", "_", "+", "@", O}. On a dot in the domain the machine cannot yet tell
whether the top-level domain starts there, so the natural design is a 9-state **NFA that
guesses**: from e4 a dot leads both to e3 (another label follows) and to e6 (the TLD follows).

![E-mail NFA](docs/diagrams/email_nfa.png)

Subset construction gives a DFA with 9 live states plus the empty-set (trap) state.
Minimisation merges {e0} with {e2}: at the very start and right after a separator in the
local part the machine needs exactly the same thing next, an alphanumeric. The result has
8 live states plus the trap.

![Minimal e-mail DFA](docs/diagrams/email_dfa.png)

| state | NFA subset(s) | meaning |
|---|---|---|
| m0 | {e0}, {e2} | start of a local-part word |
| m1 | {e1} | inside a local-part word |
| m2 | {e3} | just read `@` |
| m3 | {e4} | inside a domain label |
| m4 | {e3, e6} | just read a `.` in the domain |
| m5 | {e5} | inside a run of `-` |
| m6 | {e4, e7} | one letter after the last dot |
| m7 | {e4, e8} | ≥ 2 letters after the last dot: **accept** |

```
$ python -m fa_validators.cli email jaisri@srm.c0m
E-mail format (minimal DFA) on 'jaisri@srm.c0m'
   ...
  11. δ(m3, '.' -> DOT) = m4
  12. δ(m4, 'c' -> L) = m6
  13. δ(m6, '0' -> D) = m3
  14. δ(m3, 'm' -> L) = m3
  final state m3 -> REJECTED
```

The digit in the TLD sends m6 back to m3, so the address is rejected.

## Test cases

| Application | Accepted | Rejected |
|---|---|---|
| ATM PIN | 5309, 0007, 2468, 9999, 1020, 3141 | 530, 53091, 53o9, `53 09`, ε, +5309, 5.309, abcd |
| Card lock | ε, C, W, WW, WWC, WCWCWW, CWWCWW | WWW, CWWW, WWWC, WCWWW, WWWWC |
| Password | Tiger#2026, Mango9Pie, aB3$efgh, Chennai_88x, Zq7!Zq7!Zq7!, Trich1Tower | tiger#2026, TIGER#2026, Tiger#Mango, Tiger2026Tiger (14 chars), Tg#1, `Tiger #2026`, Abcdefgh1xyz9 (13 chars) |
| E-mail | jaisri@srmist.edu.in, ra2411026050248@srmist.edu.in, web_dev+ngo@mail.org, a-b.c@my-site.co, x@y.io | jaisri@srmist, .jaisri@mail.com, jaisri..s@mail.com, jaisri@-srm.in, jaisri@srm.c0m, jaisri@@mail.com, jaisri@srm.c |

Beyond these strings, the 14 automated checks in `tests/test_validators.py` compare each
automaton with an independently written rule or regex:

* all 5 461 strings up to length 6 over {0, 7, a, space} for the PIN DFAs;
* all 111 111 digit strings up to length 5 for the "not all equal" rule;
* all 8 191 event strings up to length 12 for the card lock;
* 60 000 random strings for the password (component DFAs, product and minimal DFA must all agree);
* every one of the 960 800 strings up to length 7 over {a, 1, `.`, `-`, `_`, `+`, `@`} for the e-mail NFA and minimal DFA;
* exact language equivalence of the subset DFA and the minimal DFA, and of the password product and its minimisation.

## When a finite automaton is enough, and when it is not

* **Enough** when the rule needs only bounded memory: a count up to a fixed limit, which
  character classes have appeared, or which part of the string is being read. The check is
  a single pass with constant memory, ideal for a kiosk or as-you-type feedback.
* **Not enough** when the rule needs outside data (the stored PIN, a DNS lookup, a breach
  list) or unbounded counting. "As many digits as letters" is not regular by the pumping
  lemma, and neither is the nested comment syntax of full RFC 5322.
* **Regular but costly** when a value rule is folded into the machine: the "not all equal"
  PIN rule took the DFA from 6 to 35 states, and the combined password machine has 81
  states against 22 for the separate checks. A small counter or lookup beside the DFA is
  the better engineering choice.

**SDG 9 (design alignment):** constant-memory validators are cheap enough to run on
low-cost kiosks and inside the browser, which supports reliable digital infrastructure.

## Layout

```
fa_validators/automata.py    DFA, NFA, subset construction, product, minimisation, DOT export
fa_validators/validators.py  the three applications, their test strings and limitations
fa_validators/cli.py         terminal demo (tables, traces, state counts, limitations)
tests/test_validators.py     14 checks (listed examples + exhaustive cross-checks)
tools/make_diagrams.py       builds docs/diagrams/*, docs/automata.json and docs/index.html
docs/                        diagrams and the browser demo
```

## References

1. J. E. Hopcroft, R. Motwani and J. D. Ullman, *Introduction to Automata Theory, Languages, and Computation*, 3rd ed., Pearson, 2007.
2. M. Sipser, *Introduction to the Theory of Computation*, 3rd ed., Cengage Learning, 2013.
3. P. A. Grassi et al., *NIST SP 800-63B, Digital Identity Guidelines*, 2017.
4. P. Resnick, Ed., "Internet Message Format," IETF RFC 5322, 2008.
