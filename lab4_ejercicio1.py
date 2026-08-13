import graphviz

# ---------- Estado del AFN ----------
class State:
    def __init__(self, id):
        self.id = id
        self.transitions = {}  # simbolo (o None para epsilon) -> lista de States

state_counter = 0

def new_state():
    global state_counter
    s = State(state_counter)
    state_counter += 1
    return s

def add_edge(s_from, symbol, s_to):
    s_from.transitions.setdefault(symbol, []).append(s_to)


# ---------- Parser (gramática recursiva descendente) ----------
# regex  := term ('|' term)*
# term   := factor+           (concatenación implícita)
# factor := base ('*' | '+' | '?')*
# base   := 'ε' | simbolo | '(' regex ')'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        c = self.tokens[self.pos]
        self.pos += 1
        return c

    def parse(self):
        node = self.parse_regex()
        return node

    def parse_regex(self):
        node = self.parse_term()
        while self.peek() == '|':
            self.advance()
            right = self.parse_term()
            node = ('union', node, right)
        return node

    def parse_term(self):
        factors = []
        while self.peek() is not None and self.peek() not in (')', '|'):
            factors.append(self.parse_factor())

        if not factors:
            return ('eps',)

        node = factors[0]
        for f in factors[1:]:
            node = ('concat', node, f)

        return node

    def parse_factor(self):
        node = self.parse_base()

        while self.peek() in ('*', '+', '?'):
            op = self.advance()

            if op == '*':
                node = ('star', node)
            elif op == '+':
                node = ('plus', node)
            elif op == '?':
                node = ('question', node)

        return node

    def parse_base(self):
        c = self.advance()

        if c == '(':
            node = self.parse_regex()

            if self.peek() == ')':
                self.advance()

            return node

        elif c == 'ε':
            return ('eps',)

        else:
            return ('char', c)


# ---------- Algoritmo de Thompson ----------
def thompson(node):
    kind = node[0]

    if kind == 'char':
        s0, s1 = new_state(), new_state()
        add_edge(s0, node[1], s1)
        return (s0, s1)

    if kind == 'eps':
        s0, s1 = new_state(), new_state()
        add_edge(s0, None, s1)
        return (s0, s1)

    if kind == 'concat':
        f1 = thompson(node[1])
        f2 = thompson(node[2])

        add_edge(f1[1], None, f2[0])

        return (f1[0], f2[1])

    if kind == 'union':
        f1 = thompson(node[1])
        f2 = thompson(node[2])

        s0, s1 = new_state(), new_state()

        add_edge(s0, None, f1[0])
        add_edge(s0, None, f2[0])

        add_edge(f1[1], None, s1)
        add_edge(f2[1], None, s1)

        return (s0, s1)

    if kind == 'star':
        f = thompson(node[1])

        s0, s1 = new_state(), new_state()

        add_edge(s0, None, f[0])
        add_edge(s0, None, s1)

        add_edge(f[1], None, f[0])
        add_edge(f[1], None, s1)

        return (s0, s1)

    if kind == 'plus':
        f = thompson(node[1])

        s0, s1 = new_state(), new_state()

        add_edge(s0, None, f[0])
        add_edge(f[1], None, f[0])
        add_edge(f[1], None, s1)

        return (s0, s1)

    if kind == 'question':
        f = thompson(node[1])

        s0, s1 = new_state(), new_state()

        add_edge(s0, None, f[0])
        add_edge(s0, None, s1)
        add_edge(f[1], None, s1)

        return (s0, s1)


# ---------- Dibujar el AFN ----------
def collect_states(start):
    visited = set()
    stack = [start]

    while stack:
        s = stack.pop()

        if s in visited:
            continue

        visited.add(s)

        for targets in s.transitions.values():
            for t in targets:
                if t not in visited:
                    stack.append(t)

    return visited


def draw_nfa(start, accept, filename):
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR')

    states = collect_states(start)

    for s in states:
        shape = 'doublecircle' if s is accept else 'circle'
        dot.node(str(s.id), shape=shape)

    # flechita de "inicio"
    dot.node('start', shape='point')
    dot.edge('start', str(start.id))

    for s in states:
        for symbol, targets in s.transitions.items():
            label = 'ε' if symbol is None else symbol

            for t in targets:
                dot.edge(str(s.id), str(t.id), label=label)

    dot.render(filename, format='png', cleanup=True)

    print(f"  -> Imagen guardada como {filename}.png")


# ---------- Simulación del AFN ----------
def epsilon_closure(states):
    stack = list(states)
    closure = set(states)

    while stack:
        s = stack.pop()

        for nxt in s.transitions.get(None, []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)

    return closure


def simulate(start, accept, w):
    current = epsilon_closure({start})

    for ch in w:
        next_states = set()

        for s in current:
            next_states.update(s.transitions.get(ch, []))

        current = epsilon_closure(next_states)

    return accept in current


# ---------- Main ----------
def main():
    global state_counter

    with open('expresiones.txt', 'r', encoding='utf-8') as f:
        lineas = [line.strip() for line in f if line.strip()]

    for i, linea in enumerate(lineas, start=1):
        regex, w = linea.split(';')
        regex = regex.strip()
        w = w.strip()

        state_counter = 0
        regex_clean = regex.replace(' ', '')
        tokens = list(regex_clean)

        parser = Parser(tokens)
        tree = parser.parse()
        start, accept = thompson(tree)

        print(f"\nAFN #{i} para r = {regex}")
        draw_nfa(start, accept, f'afn_{i}')

        acepta = simulate(start, accept, w)
        print(f"Cadena w = '{w}' -> {'sí' if acepta else 'no'}")

main()