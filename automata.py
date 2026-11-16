"""
A small finite-automata library written for Task 2.

The validators never look at raw characters directly. Each machine reads
*character classes* (for example D = any digit) and comes with a one-line
classifier that turns a typed character into its class. That keeps the
alphabets, and therefore the diagrams, small.

What is here:
  * DFA         - total transition function (missing moves go to a trap),
                  step-by-step trace of every run
  * NFA         - without epsilon moves, plus the subset construction
  * product     - intersection of DFAs (regular languages are closed under it)
  * minimise    - Moore partition refinement on the reachable part
  * equivalent  - exact language-equality test via the product machine
  * to_dot      - Graphviz export for the diagrams in docs/
"""
import re
from collections import deque
from itertools import product as _cartesian

TRAP = "trap"


def natural_key(name):
    """Sort q2 before q10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(name))]


class DFA:
    def __init__(self, name, alphabet, delta, start, accepting, classify,
                 states=None, meaning=None):
        """
        alphabet  : list of class symbols, e.g. ["D", "O"]
        delta     : {(state, symbol): next_state}; every missing pair goes to TRAP
        accepting : set of accepting states
        classify  : function char -> class symbol
        meaning   : optional {state: short description} used by the CLI
        """
        self.name = name
        self.alphabet = list(alphabet)
        self.start = start
        self.accepting = set(accepting)
        self.classify = classify
        self.meaning = dict(meaning or {})

        listed = {start} | self.accepting
        for (p, _), q in delta.items():
            listed.update((p, q))
        if states is not None:
            listed.update(states)
        self.delta = dict(delta)
        missing = [(p, a) for p in listed for a in self.alphabet if (p, a) not in self.delta]
        for key in missing:
            self.delta[key] = TRAP
        if missing or TRAP in listed:
            listed.add(TRAP)
            for a in self.alphabet:
                self.delta[(TRAP, a)] = TRAP
        order = list(states) if states is not None else sorted(listed - {TRAP}, key=natural_key)
        self.states = [s for s in order if s != TRAP] + ([TRAP] if TRAP in listed else [])

    # ------------------------------------------------------------- running
    def step(self, state, symbol):
        return self.delta.get((state, symbol), TRAP)

    def run(self, text):
        """Return (accepted, trace); trace rows are (state, char, class, next)."""
        state, trace = self.start, []
        for ch in text:
            sym = self.classify(ch)
            nxt = self.step(state, sym) if sym in self.alphabet else TRAP
            trace.append((state, ch, sym, nxt))
            state = nxt
        return state in self.accepting, trace

    def accepts(self, text):
        return self.run(text)[0]

    def accepts_symbols(self, symbols):
        state = self.start
        for s in symbols:
            state = self.step(state, s)
        return state in self.accepting

    # ------------------------------------------------------------ counting
    def reachable(self):
        seen, todo = {self.start}, deque([self.start])
        while todo:
            p = todo.popleft()
            for a in self.alphabet:
                q = self.step(p, a)
                if q not in seen:
                    seen.add(q)
                    todo.append(q)
        return seen

    def size(self):
        """Number of reachable states, trap included (the count used in the report)."""
        return len(self.reachable())

    def live_states(self):
        """Reachable states from which an accepting state can still be reached."""
        reach = self.reachable()
        alive = {s for s in reach if s in self.accepting}
        grew = True
        while grew:
            grew = False
            for s in reach - alive:
                if any(self.step(s, a) in alive for a in self.alphabet):
                    alive.add(s)
                    grew = True
        return len(alive)

    # ------------------------------------------------------------- algebra
    def product(self, other, name=None):
        """Intersection by the product construction (reachable part only)."""
        if self.alphabet != other.alphabet:
            raise ValueError("product needs a shared alphabet")
        start = (self.start, other.start)
        seen, todo, delta = {start}, deque([start]), {}
        while todo:
            p, q = todo.popleft()
            for a in self.alphabet:
                nxt = (self.step(p, a), other.step(q, a))
                delta[((p, q), a)] = nxt
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        label = {s: _pair_name(s) for s in seen}
        acc = {label[s] for s in seen if s[0] in self.accepting and s[1] in other.accepting}
        return DFA(name or f"{self.name} x {other.name}", self.alphabet,
                   {(label[p], a): label[q] for (p, a), q in delta.items()},
                   label[start], acc, self.classify,
                   states=[label[s] for s in _bfs_order(start, delta, self.alphabet)])

    def complement(self, name=None):
        return DFA(name or "not " + self.name, self.alphabet, dict(self.delta), self.start,
                   set(self.states) - self.accepting, self.classify, states=self.states)

    def minimise(self, name=None, prefix="m"):
        """Moore's algorithm: start from {accepting, non-accepting} and split
        blocks until every block is closed under the transitions."""
        states = sorted(self.reachable(), key=natural_key)
        block = {s: int(s in self.accepting) for s in states}
        while True:
            sig = {s: (block[s],) + tuple(block[self.step(s, a)] for a in self.alphabet)
                   for s in states}
            ids = {}
            new_block = {s: ids.setdefault(sig[s], len(ids)) for s in states}
            if len(ids) == len(set(block.values())):
                break
            block = new_block
        # one representative per block, blocks numbered in BFS order from the start
        rep = {}
        for s in states:
            rep.setdefault(block[s], s)
        order, seen, todo = [], {block[self.start]}, deque([block[self.start]])
        while todo:
            b = todo.popleft()
            order.append(b)
            for a in self.alphabet:
                nb = block[self.step(rep[b], a)]
                if nb not in seen:
                    seen.add(nb)
                    todo.append(nb)
        dead = [b for b in order if rep[b] not in self.accepting and
                all(block[self.step(rep[b], a)] == b for a in self.alphabet)]
        names, k = {}, 0
        for b in order:
            if dead and b == dead[0]:
                names[b] = TRAP
            else:
                names[b] = f"{prefix}{k}"
                k += 1
        delta = {(names[b], a): names[block[self.step(rep[b], a)]]
                 for b in order for a in self.alphabet}
        acc = {names[b] for b in order if rep[b] in self.accepting}
        members = {names[b]: sorted((s for s in states if block[s] == b), key=natural_key)
                   for b in order}
        m = DFA(name or self.name + " (minimal)", self.alphabet, delta,
                names[block[self.start]], acc, self.classify,
                states=[names[b] for b in order])
        m.members = members
        return m

    # -------------------------------------------------------------- export
    def to_dot(self, show_trap=False, edge_names=None, rankdir="LR"):
        edge_names = edge_names or {}
        lines = [f'digraph "{self.name}" {{', f"  rankdir={rankdir}; bgcolor=white;",
                 '  node [shape=circle fontname="Helvetica" fontsize=11];',
                 '  edge [fontname="Helvetica" fontsize=10];',
                 "  start [shape=point width=0.08];"]
        shown = [s for s in self.states if show_trap or s != TRAP]
        for s in shown:
            shape = "doublecircle" if s in self.accepting else "circle"
            lines.append(f'  "{s}" [shape={shape}];')
        lines.append(f'  start -> "{self.start}";')
        edges = {}
        for p in shown:
            for a in self.alphabet:
                q = self.step(p, a)
                label = edge_names.get(a, a)
                if q in shown and label not in edges.get((p, q), []):
                    edges.setdefault((p, q), []).append(label)
        for (p, q), syms in edges.items():
            lines.append(f'  "{p}" -> "{q}" [label="{_compress(syms)}"];')
        lines.append("}")
        return "\n".join(lines)

    def table(self):
        rows = []
        for s in self.states:
            mark = ("->" if s == self.start else "  ") + ("*" if s in self.accepting else " ")
            rows.append([mark + s] + [self.step(s, a) for a in self.alphabet])
        return rows


class NFA:
    """NFA without epsilon moves: delta maps (state, symbol) to a set of states."""

    def __init__(self, name, alphabet, delta, start, accepting, classify):
        self.name = name
        self.alphabet = list(alphabet)
        self.delta = {k: set(v) for k, v in delta.items()}
        self.start = start
        self.accepting = set(accepting)
        self.classify = classify
        found = {start} | self.accepting
        for (p, _), qs in self.delta.items():
            found.add(p)
            found |= qs
        self.states = sorted(found, key=natural_key)

    def move(self, current, symbol):
        out = set()
        for p in current:
            out |= self.delta.get((p, symbol), set())
        return out

    def accepts(self, text):
        current = {self.start}
        for ch in text:
            current = self.move(current, self.classify(ch))
            if not current:
                return False
        return bool(current & self.accepting)

    def subset_construction(self, name=None):
        """DFA whose states are sets of NFA states; the empty set is the trap."""
        def label(S):
            return "{" + ",".join(sorted(S, key=natural_key)) + "}" if S else TRAP
        start = frozenset([self.start])
        seen, todo, delta, order = {start}, deque([start]), {}, [start]
        while todo:
            S = todo.popleft()
            for a in self.alphabet:
                T = frozenset(self.move(S, a))
                delta[(label(S), a)] = label(T)
                if T and T not in seen:
                    seen.add(T)
                    order.append(T)
                    todo.append(T)
        acc = {label(S) for S in seen if S & self.accepting}
        return DFA(name or self.name + " (subset construction)", self.alphabet, delta,
                   label(start), acc, self.classify, states=[label(S) for S in order])

    def to_dot(self, edge_names=None, rankdir="LR"):
        edge_names = edge_names or {}
        lines = [f'digraph "{self.name}" {{', f"  rankdir={rankdir}; bgcolor=white;",
                 '  node [shape=circle fontname="Helvetica" fontsize=11];',
                 '  edge [fontname="Helvetica" fontsize=10];',
                 "  start [shape=point width=0.08];"]
        for s in self.states:
            lines.append(f'  "{s}" [shape={"doublecircle" if s in self.accepting else "circle"}];')
        lines.append(f'  start -> "{self.start}";')
        edges = {}
        for (p, a), qs in self.delta.items():
            for q in qs:
                edges.setdefault((p, q), []).append(edge_names.get(a, a))
        for (p, q), syms in edges.items():
            lines.append(f'  "{p}" -> "{q}" [label="{", ".join(syms)}"];')
        lines.append("}")
        return "\n".join(lines)


def equivalent(d1, d2):
    """Exact test L(d1) == L(d2). Returns (True, None) or (False, shortest counterexample)."""
    start = (d1.start, d2.start)
    word = {start: []}
    todo = deque([start])
    while todo:
        p, q = todo.popleft()
        if (p in d1.accepting) != (q in d2.accepting):
            return False, word[(p, q)]
        for a in d1.alphabet:
            nxt = (d1.step(p, a), d2.step(q, a))
            if nxt not in word:
                word[nxt] = word[(p, q)] + [a]
                todo.append(nxt)
    return True, None


def all_strings(symbols, max_len):
    """Every string over `symbols` of length 0 .. max_len."""
    for n in range(max_len + 1):
        for t in _cartesian(symbols, repeat=n):
            yield "".join(t)


def _compress(labels):
    """Write runs of single digits as ranges, e.g. 0, 1, 2, 3, 7 -> 0-3, 7."""
    digits = sorted(int(x) for x in labels if len(x) == 1 and x.isdigit())
    others = [x for x in labels if not (len(x) == 1 and x.isdigit())]
    runs, k = [], 0
    while k < len(digits):
        j = k
        while j + 1 < len(digits) and digits[j + 1] == digits[j] + 1:
            j += 1
        runs.append(str(digits[k]) if j == k else f"{digits[k]}-{digits[j]}")
        k = j + 1
    return ", ".join(runs + others)


def _pair_name(s):
    return "|".join(_pair_name(x) if isinstance(x, tuple) else str(x) for x in s)


def _bfs_order(start, delta, alphabet):
    order, seen, todo = [], {start}, deque([start])
    while todo:
        p = todo.popleft()
        order.append(p)
        for a in alphabet:
            q = delta[(p, a)]
            if q not in seen:
                seen.add(q)
                todo.append(q)
    return order
