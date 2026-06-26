#!/usr/bin/env bash
#
# run_tests.sh — assemble and execute the SimpleProc-8 test suite from scratch.
#
# For every tests/*.asm it:
#   1. assembles it fresh into a throwaway build directory, then
#   2. runs the resulting binary through the interpreter.
#
# A test passes (✓) only if it assembles cleanly AND the program halts via
# HLT without crashing or hitting the interpreter's instruction cap. The
# number of instructions executed is reported alongside each result.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
ASM="$ROOT/SimpleProc8_asm.py"
INT="$ROOT/SimpleProc8_int.py"
TESTDIR="$ROOT/tests"
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT

TICK=$'\xe2\x9c\x93'   # ✓
CROSS=$'\xe2\x9c\x97'  # ✗

pass=0
fail=0

printf '%-18s  %-8s  %-6s  %s\n' "TEST" "ASSEMBLE" "RUN" "INSTRUCTIONS"
printf '%-18s  %-8s  %-6s  %s\n' "------------------" "--------" "------" "------------"

for asm in "$TESTDIR"/*.asm; do
    base="$(basename "$asm" .asm)"
    bin="$BUILD/$base.zz"

    # 1. Assemble
    if ! "$PY" "$ASM" "$asm" -o "$bin" >/dev/null 2>&1; then
        printf '%-18s  %-8s  %-6s  %s\n' "$base" "$CROSS" "-" "-"
        fail=$((fail + 1))
        continue
    fi

    # 2. Execute
    out="$("$PY" "$INT" "$bin" 2>&1)"
    insns="$(printf '%s\n' "$out" | sed -n 's/.*Total instructions executed: \([0-9]*\).*/\1/p' | tail -1)"
    [ -z "$insns" ] && insns="?"

    if printf '%s\n' "$out" | grep -qE "Maximum instructions|Traceback|Error:"; then
        printf '%-18s  %-8s  %-6s  %s\n' "$base" "$TICK" "$CROSS" "$insns"
        fail=$((fail + 1))
    else
        printf '%-18s  %-8s  %-6s  %s\n' "$base" "$TICK" "$TICK" "$insns"
        pass=$((pass + 1))
    fi
done

echo
echo "Passed: $pass   Failed: $fail   Total: $((pass + fail))"
[ "$fail" -eq 0 ]
