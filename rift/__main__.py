"""Entry point for rift: REPL or run a .rf file."""

from __future__ import annotations

import sys
from pathlib import Path

from rift.interpreter import Interpreter
from rift.parser import Parser
from rift.resolver import Resolver
from rift.scanner import Scanner
from rift.errors import RiftRuntimeError


def run(source: str, interpreter: Interpreter | None = None) -> bool:
    """Run source code. Returns False if any scan/parse/resolve error occurred."""
    if interpreter is None:
        interpreter = Interpreter()

    scanner = Scanner(source)
    scanner.scan_tokens()
    if scanner.errors:
        for err in scanner.errors:
            print(err, file=sys.stderr)
        return False

    parser = Parser(scanner.tokens)
    try:
        statements = parser.parse()
    except Exception:
        for err in parser.errors:
            print(err, file=sys.stderr)
        return False
    if parser.errors:
        for err in parser.errors:
            print(err, file=sys.stderr)
        return False

    resolver = Resolver(interpreter)
    resolver.resolve(statements)
    if resolver.errors:
        for err in resolver.errors:
            print(err, file=sys.stderr)
        return False

    try:
        interpreter.interpret(statements)
    except RiftRuntimeError as e:
        print(e, file=sys.stderr)
        return False
    return True


def run_file(path: str) -> None:
    """Read and run a .rf file."""
    p = Path(path)
    if not p.exists():
        print(f"rift: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    source = p.read_text(encoding="utf-8")
    ok = run(source)
    sys.exit(0 if ok else 1)


def run_prompt() -> None:
    """Interactive REPL."""
    interpreter = Interpreter()
    print("Rift 0.1.0 — type exit or quit to leave")
    buf: list[str] = []
    while True:
        try:
            if buf:
                prompt = "... "
            else:
                prompt = "> "
            line = input(prompt)
        except EOFError:
            print()
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        buf.append(line)
        source = "\n".join(buf)
        # try to parse; if we get a complete statement list, run and clear buffer
        scanner = Scanner(source)
        scanner.scan_tokens()
        if scanner.errors:
            continue
        parser = Parser(scanner.tokens)
        try:
            statements = parser.parse()
        except Exception:
            if not parser.errors and not buf:
                break
            continue
        if parser.errors:
            continue
        resolver = Resolver(interpreter)
        resolver.resolve(statements)
        if resolver.errors:
            for err in resolver.errors:
                print(err, file=sys.stderr)
            buf.clear()
            continue
        buf.clear()
        try:
            interpreter.interpret(statements)
        except RiftRuntimeError as e:
            print(e, file=sys.stderr)


def main() -> None:
    argv = sys.argv[1:]
    if len(argv) == 0:
        run_prompt()
    elif len(argv) == 1:
        run_file(argv[0])
    else:
        print("usage: rift [script.rf]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
