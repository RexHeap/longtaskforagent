"""Tests for scripts/apply_tool_bindings.py"""
import json
import sys
from pathlib import Path

import pytest

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from apply_tool_bindings import (
    UI_DEFAULTS,
    apply_substitutions,
    build_substitution_map,
    render_blocks,
    render_template,
)


# ---------------------------------------------------------------------------
# build_substitution_map
# ---------------------------------------------------------------------------

class TestBuildSubstitutionMap:
    def test_defaults_when_no_bindings(self):
        subs = build_substitution_map(None)
        assert subs["__CAP_UI_PLATFORM__"] == "Chrome DevTools MCP"
        assert subs["__CAP_UI_NAVIGATE__"] == "navigate_page"
        assert subs["__CAP_UI_EVAL__"] == "evaluate_script"
        assert subs["__CAP_UI_CONSOLE__"] == "list_console_messages"

    def test_enterprise_tool_names_from_bindings(self):
        bindings = {
            "mcp_servers": {"acme_browser": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {
                        "navigate_page": "acme_browser__navigate",
                        "click": "acme_browser__click",
                        "evaluate_script": "acme_browser__eval",
                        "list_console_messages": "acme_browser__console",
                    },
                }
            },
        }
        subs = build_substitution_map(bindings)
        assert subs["__CAP_UI_NAVIGATE__"] == "acme_browser__navigate"
        assert subs["__CAP_UI_CLICK__"] == "acme_browser__click"
        assert subs["__CAP_UI_EVAL__"] == "acme_browser__eval"
        assert subs["__CAP_UI_CONSOLE__"] == "acme_browser__console"

    def test_unmapped_tools_keep_defaults(self):
        """Tools not in tool_mapping keep their default values."""
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {
                        "navigate_page": "acme__nav",
                        # hover, drag not mapped
                    },
                }
            },
        }
        subs = build_substitution_map(bindings)
        assert subs["__CAP_UI_NAVIGATE__"] == "acme__nav"
        assert subs["__CAP_UI_HOVER__"] == "hover"   # default kept
        assert subs["__CAP_UI_DRAG__"] == "drag"     # default kept

    def test_platform_name_derived_from_server(self):
        bindings = {
            "mcp_servers": {"acme_browser": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {"navigate_page": "acme_browser__navigate"},
                }
            },
        }
        subs = build_substitution_map(bindings)
        assert "acme_browser" in subs["__CAP_UI_PLATFORM__"]


# ---------------------------------------------------------------------------
# apply_substitutions
# ---------------------------------------------------------------------------

class TestApplySubstitutions:
    def test_replaces_placeholder(self):
        content = "Use `__CAP_UI_NAVIGATE__(url)` to open page."
        subs = {"__CAP_UI_NAVIGATE__": "acme_browser__navigate"}
        result = apply_substitutions(content, subs)
        assert "`acme_browser__navigate(url)`" in result
        assert "__CAP_UI_NAVIGATE__" not in result

    def test_replaces_platform_name(self):
        content = "__CAP_UI_PLATFORM__ is the mandatory tool."
        subs = {"__CAP_UI_PLATFORM__": "ACME Browser MCP"}
        result = apply_substitutions(content, subs)
        assert "ACME Browser MCP is the mandatory tool." == result

    def test_no_spurious_replacements(self):
        """Ensure only exact placeholder tokens are replaced."""
        content = "Use `evaluate_script()` for detection."
        subs = {"__CAP_UI_EVAL__": "acme__eval"}
        result = apply_substitutions(content, subs)
        # evaluate_script is NOT a placeholder — should not be replaced
        assert "evaluate_script()" in result

    def test_all_defaults_round_trip(self):
        """Rendering with defaults produces original Chrome DevTools names."""
        content = " ".join(
            f"`{v}`" for v in UI_DEFAULTS.values()
        )
        # If defaults map to themselves, round-trip is identity
        subs = build_substitution_map(None)
        rendered = apply_substitutions(
            " ".join(f"`{k}`" for k in UI_DEFAULTS.keys()),
            subs,
        )
        # Each placeholder replaced with its default value
        for placeholder, default in UI_DEFAULTS.items():
            assert f"`{default}`" in rendered


# ---------------------------------------------------------------------------
# render_blocks
# ---------------------------------------------------------------------------

class TestRenderBlocks:
    CLI_BLOCK = (
        "<!--BLOCK:capability:cli-->\n"
        "CLI content here\n"
        "<!--BLOCK:capability:mcp-->\n"
        "MCP content here\n"
        "<!--/BLOCK:capability-->"
    )

    def test_defaults_keeps_cli_block(self):
        result = render_blocks(self.CLI_BLOCK, use_mcp_block=False)
        assert "CLI content here" in result
        assert "MCP content here" not in result
        assert "<!--BLOCK" not in result

    def test_mcp_keeps_mcp_block(self):
        result = render_blocks(self.CLI_BLOCK, use_mcp_block=True)
        assert "MCP content here" in result
        assert "CLI content here" not in result
        assert "<!--BLOCK" not in result

    def test_no_block_markers_passthrough(self):
        content = "No block markers here."
        assert render_blocks(content, use_mcp_block=False) == content
        assert render_blocks(content, use_mcp_block=True) == content

    def test_multiple_blocks(self):
        content = (
            "Before\n"
            "<!--BLOCK:capability:cli-->CLI 1<!--BLOCK:capability:mcp-->MCP 1<!--/BLOCK:capability-->\n"
            "Between\n"
            "<!--BLOCK:capability:cli-->CLI 2<!--BLOCK:capability:mcp-->MCP 2<!--/BLOCK:capability-->\n"
            "After"
        )
        result = render_blocks(content, use_mcp_block=True)
        assert "MCP 1" in result
        assert "MCP 2" in result
        assert "CLI 1" not in result
        assert "CLI 2" not in result
        assert "Before" in result
        assert "Between" in result
        assert "After" in result


# ---------------------------------------------------------------------------
# render_template (integration)
# ---------------------------------------------------------------------------

class TestRenderTemplate:
    TEMPLATE_WITH_BLOCK = (
        "# __CAP_UI_PLATFORM__ Guide\n\n"
        "<!--BLOCK:capability:cli-->\n"
        "| Open page | `navigate_page(url)` |\n"
        "<!--BLOCK:capability:mcp-->\n"
        "| Open page | `__CAP_UI_NAVIGATE__(url)` |\n"
        "<!--/BLOCK:capability-->\n\n"
        "Use `__CAP_UI_EVAL__` for error detection."
    )

    def test_defaults_rendering(self):
        result = render_template(self.TEMPLATE_WITH_BLOCK, bindings=None)
        assert "Chrome DevTools MCP Guide" in result
        assert "| Open page | `navigate_page(url)` |" in result
        assert "__CAP_UI_NAVIGATE__" not in result
        assert "`evaluate_script`" in result

    def test_mcp_rendering_with_bindings(self):
        bindings = {
            "mcp_servers": {"acme_browser": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {
                        "navigate_page": "acme_browser__navigate",
                        "evaluate_script": "acme_browser__eval",
                    },
                }
            },
        }
        result = render_template(self.TEMPLATE_WITH_BLOCK, bindings=bindings)
        assert "| Open page | `acme_browser__navigate(url)` |" in result
        assert "navigate_page" not in result
        assert "`acme_browser__eval`" in result
        assert "__CAP_UI_NAVIGATE__" not in result
        assert "__CAP_UI_EVAL__" not in result

    def test_no_remaining_placeholders_after_defaults(self):
        """After defaults rendering, no __CAP_*__ tokens should remain."""
        result = render_template(self.TEMPLATE_WITH_BLOCK, bindings=None)
        assert "__CAP_" not in result

    def test_bindings_without_ui_tools_uses_cli_block(self):
        """If bindings have no ui_tools.tool_mapping, CLI block is selected."""
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {},
        }
        result = render_template(self.TEMPLATE_WITH_BLOCK, bindings=bindings)
        assert "| Open page | `navigate_page(url)` |" in result


# ---------------------------------------------------------------------------
# find_plugin_root / find_templates (smoke test)
# ---------------------------------------------------------------------------

class TestFindTemplates:
    def test_plugin_root_exists(self):
        from apply_tool_bindings import find_plugin_root
        root = find_plugin_root()
        assert root.exists()
        assert (root / "scripts").exists()

    def test_templates_found(self):
        from apply_tool_bindings import find_plugin_root, find_templates
        root = find_plugin_root()
        templates = find_templates(root)
        # Should find at least 6 templates
        assert len(templates) >= 6

    def test_template_output_paths_are_md_files(self):
        from apply_tool_bindings import find_plugin_root, find_templates
        root = find_plugin_root()
        for tmpl_path, rel_out in find_templates(root):
            assert tmpl_path.suffix == ".template"
            assert rel_out.suffix == ".md"
