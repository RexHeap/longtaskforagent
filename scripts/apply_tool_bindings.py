#!/usr/bin/env python3
"""
Render SKILL.md.template files into .long-task-bindings/ using tool-bindings.json.

Templates use two mechanisms:
1. BLOCK markers — select between CLI and MCP sections:
      <!--BLOCK:capability:cli-->
      ...default CLI content...
      <!--BLOCK:capability:mcp-->
      ...enterprise MCP content (with __CAP_UI_*__ placeholders)...
      <!--/BLOCK:capability-->

2. Placeholder substitution — __CAP_UI_NAVIGATE__ etc. replaced with actual
   tool names from tool-bindings.json (or defaults for Chrome DevTools MCP).

Rendered .md files are written to the project-local output directory
(default: .long-task-bindings/), NOT to the plugin directory.  This avoids
concurrent-session race conditions when multiple projects are open.

Usage:
    python scripts/apply_tool_bindings.py tool-bindings.json
    python scripts/apply_tool_bindings.py tool-bindings.json --output-dir .long-task-bindings
    python scripts/apply_tool_bindings.py tool-bindings.json --dry-run
    python scripts/apply_tool_bindings.py --defaults
    python scripts/apply_tool_bindings.py --quiet   # warnings to stderr, no abort

Exit codes:
    0 — all templates rendered successfully
    1 — one or more errors (unless --quiet)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Placeholder defaults (Chrome DevTools MCP tool names)
# ---------------------------------------------------------------------------

UI_DEFAULTS: dict[str, str] = {
    "__CAP_UI_PLATFORM__":    "Chrome DevTools MCP",
    "__CAP_UI_NAVIGATE__":    "navigate_page",
    "__CAP_UI_WAIT__":        "wait_for",
    "__CAP_UI_SNAPSHOT__":    "take_snapshot",
    "__CAP_UI_SCREENSHOT__":  "take_screenshot",
    "__CAP_UI_CLICK__":       "click",
    "__CAP_UI_FILL__":        "fill",
    "__CAP_UI_KEY__":         "press_key",
    "__CAP_UI_EVAL__":        "evaluate_script",
    "__CAP_UI_CONSOLE__":     "list_console_messages",
    "__CAP_UI_HOVER__":       "hover",
    "__CAP_UI_DRAG__":        "drag",
    "__CAP_UI_NETWORK__":     "list_network_requests",
}

# Mapping from tool-bindings.json ui_tools.tool_mapping keys → placeholder names
_TOOL_MAPPING_KEYS: dict[str, str] = {
    "navigate_page":         "__CAP_UI_NAVIGATE__",
    "wait_for":              "__CAP_UI_WAIT__",
    "take_snapshot":         "__CAP_UI_SNAPSHOT__",
    "take_screenshot":       "__CAP_UI_SCREENSHOT__",
    "click":                 "__CAP_UI_CLICK__",
    "fill":                  "__CAP_UI_FILL__",
    "press_key":             "__CAP_UI_KEY__",
    "evaluate_script":       "__CAP_UI_EVAL__",
    "list_console_messages": "__CAP_UI_CONSOLE__",
    "hover":                 "__CAP_UI_HOVER__",
    "drag":                  "__CAP_UI_DRAG__",
    "list_network_requests": "__CAP_UI_NETWORK__",
}

# Regex for BLOCK markers (non-greedy, non-DOTALL within each block segment)
_BLOCK_RE = re.compile(
    r'<!--BLOCK:capability:cli-->(.*?)<!--BLOCK:capability:mcp-->(.*?)<!--/BLOCK:capability-->',
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Core rendering
# ---------------------------------------------------------------------------

def build_substitution_map(bindings: dict | None) -> dict[str, str]:
    """
    Build placeholder → replacement map from tool-bindings.json or defaults.

    Args:
        bindings: Parsed tool-bindings.json dict, or None for defaults.

    Returns:
        Dict mapping __CAP_*__ → actual value.
    """
    subs = dict(UI_DEFAULTS)  # start with defaults

    if bindings is None:
        return subs

    ui_tools = bindings.get("capability_bindings", {}).get("ui_tools", {})
    tool_mapping = ui_tools.get("tool_mapping", {})

    # Resolve enterprise tool names
    for canonical_name, placeholder in _TOOL_MAPPING_KEYS.items():
        if canonical_name in tool_mapping:
            subs[placeholder] = tool_mapping[canonical_name]

    # Platform name: derive from first ui_tools server name
    server_name = ui_tools.get("tool_mapping", {})
    mcp_servers = bindings.get("mcp_servers", {})
    if mcp_servers:
        first_server = next(iter(mcp_servers))
        subs["__CAP_UI_PLATFORM__"] = f"{first_server} MCP"

    return subs


def render_blocks(content: str, use_mcp_block: bool) -> str:
    """
    Process BLOCK markers in content.

    When use_mcp_block=True:  keeps the MCP block, removes CLI block.
    When use_mcp_block=False: keeps the CLI block, removes MCP block.
    """
    def replacer(m: re.Match) -> str:
        cli_content = m.group(1)
        mcp_content = m.group(2)
        if use_mcp_block:
            return mcp_content
        else:
            return cli_content

    return _BLOCK_RE.sub(replacer, content)


def apply_substitutions(content: str, subs: dict[str, str]) -> str:
    """Replace all __CAP_*__ placeholders with their values."""
    for placeholder, value in subs.items():
        content = content.replace(placeholder, value)
    return content


def render_template(template_content: str, bindings: dict | None) -> str:
    """
    Render a single template file.

    Args:
        template_content: Raw .md.template file content.
        bindings: Parsed tool-bindings.json, or None for defaults.

    Returns:
        Rendered Markdown content.
    """
    use_mcp = bindings is not None and bool(
        bindings.get("capability_bindings", {}).get("ui_tools", {}).get("tool_mapping")
    )
    subs = build_substitution_map(bindings)
    content = render_blocks(template_content, use_mcp_block=use_mcp)
    content = apply_substitutions(content, subs)
    return content


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_plugin_root() -> Path:
    """Locate the plugin root directory (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def find_templates(plugin_root: Path) -> list[tuple[Path, Path]]:
    """
    Find all .md.template files and their output paths (relative to skills/).

    Returns:
        List of (template_path, relative_output_path) tuples.
        relative_output_path is relative to the output directory.
    """
    templates = []
    skills_dir = plugin_root / "skills"

    for tmpl in skills_dir.rglob("*.md.template"):
        # Output path: strip .template suffix
        rel = tmpl.relative_to(plugin_root / "skills")
        output_rel = rel.with_suffix("")  # removes .template → .md
        templates.append((tmpl, Path("skills") / output_rel))

    return templates


# ---------------------------------------------------------------------------
# Main render loop
# ---------------------------------------------------------------------------

def render_all(
    plugin_root: Path,
    output_dir: Path,
    bindings: dict | None,
    dry_run: bool = False,
    quiet: bool = False,
) -> int:
    """
    Render all templates and write to output_dir.

    Returns:
        Number of errors encountered.
    """
    templates = find_templates(plugin_root)
    if not templates:
        msg = f"No .md.template files found under {plugin_root / 'skills'}"
        print(msg, file=sys.stderr)
        return 1

    errors = 0
    rendered = 0

    for tmpl_path, rel_output in templates:
        out_path = output_dir / rel_output

        try:
            with open(tmpl_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            print(f"[apply_tool_bindings] ERROR reading {tmpl_path}: {e}",
                  file=sys.stderr)
            errors += 1
            continue

        try:
            rendered_content = render_template(raw, bindings)
        except Exception as e:  # noqa: BLE001
            print(f"[apply_tool_bindings] ERROR rendering {tmpl_path}: {e}",
                  file=sys.stderr)
            errors += 1
            continue

        if dry_run:
            print(f"[dry-run] Would write: {out_path}")
            rendered += 1
            continue

        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            rendered += 1
        except OSError as e:
            print(f"[apply_tool_bindings] ERROR writing {out_path}: {e}",
                  file=sys.stderr)
            errors += 1

    if not quiet or errors:
        label = "dry-run" if dry_run else "rendered"
        print(
            f"[apply_tool_bindings] {rendered} templates {label}"
            + (f", {errors} errors" if errors else ""),
            file=sys.stderr if quiet else sys.stdout,
        )

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render SKILL.md.template files with tool bindings"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "bindings", nargs="?", default=None,
        help="Path to tool-bindings.json (enterprise MCP mode)"
    )
    group.add_argument(
        "--defaults", action="store_true",
        help="Render with default Chrome DevTools MCP values (no tool-bindings.json needed)"
    )
    parser.add_argument(
        "--output-dir", default=".long-task-bindings",
        help="Output directory for rendered files (default: .long-task-bindings)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be written without writing files"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only output warnings/errors to stderr; suppress normal output"
    )
    args = parser.parse_args()

    plugin_root = find_plugin_root()
    output_dir = Path(args.output_dir).resolve()

    # Resolve bindings
    bindings: dict | None = None
    if args.defaults:
        bindings = None  # use defaults
    elif args.bindings:
        try:
            with open(args.bindings, "r", encoding="utf-8") as f:
                bindings = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: {args.bindings} not found", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Cannot parse {args.bindings}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # No argument and no --defaults → treat as --defaults
        bindings = None

    errors = render_all(
        plugin_root=plugin_root,
        output_dir=output_dir,
        bindings=bindings,
        dry_run=args.dry_run,
        quiet=args.quiet,
    )

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
