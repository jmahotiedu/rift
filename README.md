# Rift

A tree-walking interpreter for the Rift programming language. Variables, functions, closures, classes with inheritance, control flow, and a small standard library.

## Run

**REPL**

```bash
python -m rift
```

**Run a file**

```bash
python -m rift script.rf
```

**Examples**

```bash
python -m rift examples/fibonacci.rf
python -m rift examples/fizzbuzz.rf
python -m rift examples/counter.rf
python -m rift examples/animals.rf
python -m rift examples/linked_list.rf
```

**Example snippet**

```rift
let x = 10;
print(x + 2);

fn fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}
print(fib(10));
```

## Install

From the project root:

```bash
pip install -e .
```

Then `rift` is available as a console script (or use `python -m rift`).

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Architecture

Source text → **Scanner** (tokens) → **Parser** (recursive descent, AST) → **Resolver** (bind variables, check scope) → **Interpreter** (tree-walk, environment chain). No bytecode; each expression/statement is evaluated by traversing the AST. Closures capture the defining environment; classes bind `this` and support single inheritance with `super`.

## Tech

- Python 3.11+
- Stdlib only for the core; optional dev deps: pytest, mypy, ruff
- Scanner → Parser (recursive descent) → Resolver → Interpreter

## Future work

Bytecode compiler and VM; more types (lists, maps in-language); standard library modules; better error messages with source snippets.

## License

MIT
