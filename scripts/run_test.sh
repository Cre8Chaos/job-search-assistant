#!/usr/bin/env bash
#
# run_test.sh — spin up a throwaway test workspace from the committed sample
# persona and verify the engine against it. Lets the maintainer run/test the
# PRODUCT exactly as a brand-new user would, with ZERO personal data involved.
#
# What it does:
#   1. Resets .test-workspace/ to a fresh copy of examples/sample-workspace/.
#   2. Points JOB_SEARCH_WORKSPACE at that copy.
#   3. Runs the engine selftest (no network) and validates the workspace.
#   4. Prints the export line to drive find -> evaluate -> tailor interactively.
#
# Usage:
#   bash scripts/run_test.sh           # reset + verify, then print next steps
#   source scripts/run_test.sh         # same, but also exports the env var into
#                                      # your current shell for follow-up commands
#
# Safe to `source`: it never calls `exit` and never leaves `set -e`/`-u` behind
# in your interactive shell (those are scoped to direct execution only).

run_test_main() {
    local engine_root fixture scratch py
    engine_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    fixture="$engine_root/examples/sample-workspace"
    scratch="$engine_root/.test-workspace"
    py="$(command -v python3 || command -v python || true)"

    if [[ -z "$py" ]]; then
        echo "ERROR: no python3 or python found on PATH" >&2
        return 1
    fi
    if [[ ! -d "$fixture" ]]; then
        echo "ERROR: sample fixture missing at $fixture" >&2
        return 1
    fi

    echo "==> Resetting scratch workspace: $scratch"
    rm -rf "$scratch" || return 1
    cp -R "$fixture" "$scratch" || return 1

    export JOB_SEARCH_WORKSPACE="$scratch"

    echo "==> Engine selftest (no network)"
    "$py" "$engine_root/scripts/selftest.py" || {
        echo "ERROR: engine selftest failed" >&2
        return 1
    }

    echo "==> Validating test workspace"
    "$py" "$engine_root/scripts/workspace.py" validate || {
        echo "ERROR: workspace validate failed" >&2
        return 1
    }

    echo
    echo "Test workspace ready (fictional persona 'Jordan Rivera')."
    echo "It is a disposable copy — re-run this script anytime to reset to a clean state."
    echo
    echo "To drive the product against it in your shell, export the same path:"
    echo "    export JOB_SEARCH_WORKSPACE=\"$scratch\""
    echo
    echo "Then in Claude Code run the product skills: js-find-jobs -> js-evaluate -> js-tailor."
    return 0
}

# Sourced vs executed: when sourced, keep the exported JOB_SEARCH_WORKSPACE in the
# caller's shell and use `return` so a failure never closes their terminal. When
# executed directly, harden options and propagate the exit code.
if (return 0 2>/dev/null); then
    run_test_main
else
    set -euo pipefail
    run_test_main
    exit $?
fi
