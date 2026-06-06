#!/usr/bin/env python3
"""HERA Harness Helm enforcement scripts."""

from __future__ import annotations

import argparse
import sys

from harness_lib.archive import command_archive, command_cleanup_runs
from harness_lib.context import command_context
from harness_lib.harvest import command_harvest
from harness_lib.harvest_tag import command_harvest_tag
from harness_lib.index import command_index, command_stale
from harness_lib.install import command_install
from harness_lib.lint import command_lint
from harness_lib.new_doc import command_new_doc
from harness_lib.snapshot import REWINDABLE_STEPS, command_rewind, command_snapshot
from harness_lib.schema import load_schema
from harness_lib.templates import CANONICAL_TEMPLATES
from harness_lib.validation import (
    command_cartridge_validate,
    command_normalization_validate,
    command_reference_validate,
    command_target_smoke,
    command_template_validate,
)

LOG_START = "=== [DANDI] :: Harness Helm (_start_) ==="
LOG_END = "=== [DANDI] :: Harness Helm (__end__) ==="
# This list is the cartridge/reference validation surface, not a 1:1 list of
# local CLI subcommands. h2-context and h2-harvest are directly implemented by harness.py.
EXPECTED_COMMANDS = {
    "h2-context",
    "h2-plan",
    "h2-design",
    "h2-autorun",
    "h2-rewind",
    "h2-analysis",
    "h2-report",
    "h2-cartridge",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-compound",
    "h2-archive",
    "h2-ops",
    "h2-harvest",
    "h2-harvest-tag",
}
H2_CLI_NOTE = (
    "Note: among the h2-* lifecycle commands, h2-context and h2-harvest are directly "
    "implemented by this CLI. Use .claude/commands/h2/*, the Codex h2 skill, "
    "or .harness-helm/h2-cartridge.yml mappings for the other h2-* commands."
)


class HarnessArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "invalid choice" in message or "the following arguments are required: command" in message:
            self.print_usage(sys.stderr)
            self.exit(2, f"{self.prog}: error: {message}\n{H2_CLI_NOTE}\n")
        super().error(message)


from harness_lib.run_lifecycle import (
    INVOCATION_MODES,
    command_run_mark,
    command_run_stats,
)
def build_parser() -> argparse.ArgumentParser:
    schema = load_schema()
    stale_days = schema.get("stale_days", {})
    parser = HarnessArgumentParser(
        description="HERA Harness Helm enforcement scripts",
        epilog=H2_CLI_NOTE,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    lint = sub.add_parser("kb-lint")
    lint.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    lint.set_defaults(func=command_lint)

    index = sub.add_parser("kb-index")
    index.set_defaults(func=command_index)

    stale = sub.add_parser("kb-stale")
    stale.add_argument("--draft-days", type=int, default=int(stale_days.get("draft", 30)))
    stale.add_argument("--pending-days", type=int, default=int(stale_days.get("pending", 14)))
    stale.add_argument("--harness-raw-days", type=int, default=int(stale_days.get("harness_raw", 7)))
    stale.add_argument("--harness-normalized-days", type=int, default=int(stale_days.get("harness_normalized", 30)))
    stale.set_defaults(func=command_stale)

    cartridge = sub.add_parser("cartridge-validate")
    cartridge.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    cartridge.set_defaults(func=command_cartridge_validate)

    context = sub.add_parser("h2-context")
    context.add_argument("--feature")
    context.add_argument("--task", required=True)
    context.add_argument("--run-id")
    context.add_argument("--next")
    context.add_argument("--autorun-id")
    context.add_argument("--dry-run", action="store_true")
    context.set_defaults(func=command_context)

    harvest = sub.add_parser("h2-harvest")
    harvest_group = harvest.add_mutually_exclusive_group()
    harvest_group.add_argument("--promote")
    harvest_group.add_argument("--reject")
    harvest.add_argument("--run-id")
    harvest.add_argument("--dry-run", action="store_true")
    harvest.add_argument("--force", action="store_true")
    harvest.add_argument("--skip-raw", action="store_true")
    harvest.set_defaults(func=command_harvest)

    harvest_tag = sub.add_parser("h2-harvest-tag")
    harvest_tag.add_argument("--classification-json")
    harvest_tag.add_argument("--run-id")
    harvest_tag.add_argument("--dry-run", action="store_true")
    harvest_tag.add_argument("--autorun", action="store_true")
    harvest_tag.set_defaults(func=command_harvest_tag)

    run_mark = sub.add_parser("run-mark")
    run_mark_sub = run_mark.add_subparsers(dest="run_mark_action", required=True)
    run_mark_start = run_mark_sub.add_parser("start")
    run_mark_start.add_argument("--feature", required=True)
    run_mark_start.add_argument("--run-id", required=True)
    run_mark_start.add_argument("--command", dest="h2_command", required=True, choices=sorted(EXPECTED_COMMANDS))
    run_mark_start.add_argument("--task")
    run_mark_start.add_argument("--autorun-id")
    run_mark_start.add_argument("--invoked-surface")
    run_mark_start.add_argument("--invocation-mode", choices=sorted(INVOCATION_MODES))
    run_mark_start.set_defaults(func=command_run_mark)
    run_mark_complete = run_mark_sub.add_parser("complete")
    run_mark_complete.add_argument("--feature", required=True)
    run_mark_complete.add_argument("--run-id", required=True)
    run_mark_complete.add_argument("--status", choices=["completed", "failed", "incomplete"], default="completed")
    run_mark_complete.add_argument("--artifact", action="append")
    run_mark_complete.add_argument("--invoked-surface")
    run_mark_complete.add_argument("--invocation-mode", choices=sorted(INVOCATION_MODES))
    run_mark_complete.set_defaults(func=command_run_mark)

    run_stats = sub.add_parser("run-stats")
    run_stats.add_argument("feature", nargs="?")
    run_stats.add_argument("--limit", type=int, default=20)
    run_stats.add_argument("--json", action="store_true")
    run_stats.set_defaults(func=command_run_stats)

    snapshot = sub.add_parser("h2-snapshot")
    snapshot_sub = snapshot.add_subparsers(dest="snapshot_action", required=True)
    snapshot_save = snapshot_sub.add_parser("save")
    snapshot_save.add_argument("--feature", required=True)
    snapshot_save.add_argument("--run-id", required=True)
    snapshot_save.add_argument("--step", required=True, choices=sorted(REWINDABLE_STEPS))
    snapshot_save.add_argument("--invoked-surface")
    snapshot_save.add_argument("--invocation-mode", choices=sorted(INVOCATION_MODES))
    snapshot_save.set_defaults(func=command_snapshot)
    snapshot_list = snapshot_sub.add_parser("list")
    snapshot_list.add_argument("--feature", required=True)
    snapshot_list.add_argument("--run-id")
    snapshot_list.set_defaults(func=command_snapshot)
    snapshot_complete = snapshot_sub.add_parser("complete")
    snapshot_complete.add_argument("--feature", required=True)
    snapshot_complete.add_argument("--run-id", required=True)
    snapshot_complete.add_argument("--step", required=True, choices=sorted(REWINDABLE_STEPS))
    snapshot_complete.add_argument("--status", choices=["completed", "failed", "incomplete"], default="completed")
    snapshot_complete.add_argument("--artifact", action="append")
    snapshot_complete.add_argument("--invoked-surface")
    snapshot_complete.add_argument("--invocation-mode", choices=sorted(INVOCATION_MODES))
    snapshot_complete.set_defaults(func=command_snapshot)
    snapshot_restore = snapshot_sub.add_parser("restore")
    snapshot_restore.add_argument("--feature", required=True)
    snapshot_restore.add_argument("--run-id", required=True)
    snapshot_restore.add_argument("--step", required=True, choices=sorted(REWINDABLE_STEPS))
    snapshot_restore.add_argument("--dry-run", action="store_true")
    snapshot_restore.add_argument("--force", action="store_true")
    snapshot_restore.set_defaults(func=command_snapshot)

    rewind = sub.add_parser("h2-rewind")
    rewind.add_argument("step", choices=sorted(REWINDABLE_STEPS))
    rewind.add_argument("--feature", required=True)
    rewind.add_argument("--run-id", required=True)
    rewind.add_argument("--dry-run", action="store_true")
    rewind.add_argument("--force", action="store_true")
    rewind.set_defaults(func=command_rewind)

    templates = sub.add_parser("template-validate")
    templates.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    templates.set_defaults(func=command_template_validate)

    references = sub.add_parser("reference-validate")
    references.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    references.set_defaults(func=command_reference_validate)

    normalization = sub.add_parser("normalization-validate")
    normalization.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    normalization.set_defaults(func=command_normalization_validate)

    new_doc = sub.add_parser("new-doc")
    new_doc.add_argument("type", choices=sorted(CANONICAL_TEMPLATES))
    new_doc.add_argument("--target", help="Repository-relative output path. Defaults to the type route.")
    new_doc.add_argument("--feature")
    new_doc.add_argument("--topic")
    new_doc.add_argument("--title")
    new_doc.add_argument("--owner", default="<TODO: git username 또는 team id>")
    new_doc.add_argument("--domain", default="insurance")
    new_doc.add_argument("--area", default="project")
    new_doc.add_argument("--number", default="0001")
    new_doc.add_argument("--sequence", default="001")
    new_doc.add_argument("--status", default="draft")
    new_doc.add_argument("--dry-run", action="store_true")
    new_doc.add_argument("--force", action="store_true")
    new_doc.set_defaults(func=command_new_doc)

    archive = sub.add_parser("archive")
    archive.add_argument("feature")
    archive.add_argument("--month")
    archive.add_argument("--source-trace")
    archive.add_argument("--source-issue", help=argparse.SUPPRESS)
    archive.add_argument("--source-pr")
    archive.add_argument("--dry-run", action="store_true")
    archive.add_argument("--strict", action="store_true")
    archive.set_defaults(func=command_archive)

    cleanup = sub.add_parser("cleanup-runs")
    cleanup.add_argument("--raw-days", type=int, default=int(stale_days.get("harness_raw", 7)))
    cleanup.add_argument("--normalized-days", type=int, default=int(stale_days.get("harness_normalized", 30)))
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.set_defaults(func=command_cleanup_runs)

    target_smoke = sub.add_parser("target-smoke")
    target_smoke.add_argument("--strict", action="store_true")
    target_smoke.set_defaults(func=command_target_smoke)

    install = sub.add_parser("install")
    install.add_argument("--target", default=".", help="Target repository root (default: cwd).")
    install.add_argument("--allow-non-git", action="store_true",
                         help="Allow target without .git/.")
    install.add_argument("--dry-run", action="store_true",
                         help="Print planned actions without modifying target.")
    install.add_argument("--backup", action="store_true",
                         help="Save *.bak-{timestamp} for each file the install would overwrite.")
    install.add_argument("--quiet", action="store_true",
                         help="Suppress the final summary line.")
    install.add_argument("--manifest", help="Path to h2-install/MANIFEST.txt (default: cwd/h2-install/MANIFEST.txt).")
    install.set_defaults(func=command_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    quiet_logs = args.command == "run-stats" and getattr(args, "json", False)
    if not quiet_logs:
        print(LOG_START)
    try:
        return args.func(args)
    finally:
        if not quiet_logs:
            print(LOG_END)


if __name__ == "__main__":
    raise SystemExit(main())
