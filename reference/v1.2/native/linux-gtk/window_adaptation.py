#!/usr/bin/env python3
"""Bounded GTK4 window-adaptation reference for GLAZE UI V1.2.

This reference validates desktop window recomposition only. Window width is a
fixture/capability input; it is not used to infer device identity and does not
establish foldable hinge/posture, physical-device, production, RC, or Stable
acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

ROOT = Path(__file__).resolve().parent
CSS_PATH = ROOT / "glaze-v1.2-linux.css"
WIDE_THRESHOLD_PX = 900
MIN_WINDOW_WIDTH_PX = 520
MAX_WINDOW_WIDTH_PX = 1240
MIN_WINDOW_HEIGHT_PX = 520
MAX_WINDOW_HEIGHT_PX = 860


def bounded(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--window-width", type=int, default=1180)
    parser.add_argument("--window-height", type=int, default=760)
    parser.add_argument("--evidence-file")
    return parser.parse_args()


class GlazeWindowAdaptationCandidate(Gtk.Application):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(
            application_id="com.goreecloud.glazeui.reference.v12.linux.windowadaptation",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.args = args
        self.window: Gtk.ApplicationWindow | None = None
        self.workspace: Gtk.Box | None = None
        self.summary: Gtk.Label | None = None
        self.primary_panel: Gtk.Widget | None = None
        self.context_panel: Gtk.Widget | None = None
        self.task_entry: Gtk.Entry | None = None
        self.layout_class = "compact"
        self.panel_count = 1
        self.evidence_written = False

    def do_activate(self) -> None:
        if self.window is not None:
            self.window.present()
            return

        self._load_css()
        self.window = self._build_window()
        self.window.present()
        GLib.timeout_add(300, self._after_present)

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_path(str(CSS_PATH))
        display = Gdk.Display.get_default()
        if display is None:
            raise RuntimeError("GTK display is unavailable")
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_window(self) -> Gtk.ApplicationWindow:
        width = bounded(
            self.args.window_width,
            MIN_WINDOW_WIDTH_PX,
            MAX_WINDOW_WIDTH_PX,
        )
        height = bounded(
            self.args.window_height,
            MIN_WINDOW_HEIGHT_PX,
            MAX_WINDOW_HEIGHT_PX,
        )

        window = Gtk.ApplicationWindow(application=self)
        window.set_title("GLAZE UI V1.2 — Linux Window Adaptation Candidate")
        window.set_default_size(width, height)
        window.set_size_request(MIN_WINDOW_WIDTH_PX, MIN_WINDOW_HEIGHT_PX)
        window.add_css_class("glaze-shell")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        window.set_child(scroll)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_top(24)
        page.set_margin_bottom(24)
        page.set_margin_start(24)
        page.set_margin_end(24)
        scroll.set_child(page)

        kicker = Gtk.Label(
            label="GLAZE UI V1.2 · LINUX WINDOW ADAPTATION",
            xalign=0,
        )
        kicker.add_css_class("kicker")
        page.append(kicker)

        title = Gtk.Label(
            label="Adapt the experience, not merely the dimensions.",
            xalign=0,
        )
        title.set_wrap(True)
        title.add_css_class("title")
        page.append(title)

        self.summary = Gtk.Label(label="Window adaptation pending…", xalign=0)
        self.summary.set_wrap(True)
        self.summary.add_css_class("secondary")
        page.append(self.summary)

        self.workspace = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=16,
        )
        self.workspace.set_homogeneous(False)
        page.append(self.workspace)

        self.primary_panel = self._build_primary_panel()
        self.context_panel = self._build_context_panel()

        boundary = Gtk.Label(
            label=(
                "Boundary: bounded GTK desktop window-width fixture only. Width is "
                "not device identity. No hinge sensor/posture semantics, physical "
                "foldable qualification, production capability selection, RC, or "
                "Stable authority."
            ),
            xalign=0,
        )
        boundary.set_wrap(True)
        boundary.add_css_class("boundary")
        page.append(boundary)
        return window

    def _build_primary_panel(self) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.add_css_class("glass-base")
        panel.add_css_class("material-card")
        panel.set_hexpand(True)

        heading = Gtk.Label(label="Primary task", xalign=0)
        heading.add_css_class("section-title")
        panel.append(heading)

        body = Gtk.Label(
            label=(
                "The current work remains complete in compact mode and is retained "
                "when expanded context is available."
            ),
            xalign=0,
        )
        body.set_wrap(True)
        body.add_css_class("secondary")
        panel.append(body)

        self.task_entry = Gtk.Entry()
        self.task_entry.set_text("Research Library · current task preserved")
        self.task_entry.set_hexpand(True)
        self.task_entry.set_can_focus(True)
        panel.append(self.task_entry)
        return panel

    def _build_context_panel(self) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.add_css_class("glass-panel")
        panel.add_css_class("material-card")
        panel.set_hexpand(True)

        heading = Gtk.Label(label="Added context", xalign=0)
        heading.add_css_class("section-title")
        panel.append(heading)

        body = Gtk.Label(
            label=(
                "Expanded space adds supporting detail and an inspector-like context "
                "surface instead of merely scaling the compact task."
            ),
            xalign=0,
        )
        body.set_wrap(True)
        body.add_css_class("secondary")
        panel.append(body)

        status = Gtk.Label(
            label="Composition: primary task + contextual detail",
            xalign=0,
        )
        status.add_css_class("status-pill")
        panel.append(status)
        return panel

    def _clear_workspace(self) -> None:
        assert self.workspace is not None
        child = self.workspace.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.workspace.remove(child)
            child = next_child

    def _apply_layout(self, width: int) -> None:
        assert self.workspace is not None
        assert self.summary is not None
        assert self.primary_panel is not None
        assert self.context_panel is not None

        self._clear_workspace()
        self.workspace.append(self.primary_panel)

        wide = width >= WIDE_THRESHOLD_PX
        self.layout_class = "expanded" if wide else "compact"
        self.panel_count = 2 if wide else 1

        if wide:
            self.workspace.append(self.context_panel)

        self.summary.set_label(
            f"Runtime width: {width}px · layout: {self.layout_class} · "
            f"panels: {self.panel_count}"
        )

    def _after_present(self) -> bool:
        assert self.window is not None
        width = self.window.get_width()
        self._apply_layout(width)
        GLib.timeout_add(200, self._emit_evidence)
        return GLib.SOURCE_REMOVE

    def _emit_evidence(self) -> bool:
        if self.evidence_written:
            return GLib.SOURCE_REMOVE
        assert self.window is not None
        assert self.workspace is not None
        assert self.primary_panel is not None
        assert self.task_entry is not None

        children = 0
        child = self.workspace.get_first_child()
        while child is not None:
            children += 1
            child = child.get_next_sibling()

        width = self.window.get_width()
        height = self.window.get_height()
        task_value = self.task_entry.get_text()
        data = {
            "schemaVersion": 1,
            "product": "GLAZE UI V1.2",
            "lifecycle": "Candidate native evidence",
            "platform": "Linux GTK4",
            "evidenceKind": "bounded-window-recomposition",
            "window": {
                "width": width,
                "height": height,
                "wideThresholdPx": WIDE_THRESHOLD_PX,
            },
            "layoutClass": self.layout_class,
            "panelCount": self.panel_count,
            "runtimeWorkspaceChildren": children,
            "primaryTaskPresent": self.primary_panel.get_parent() is self.workspace,
            "primaryTaskValue": task_value,
            "addedContext": self.context_panel is not None
            and self.context_panel.get_parent() is self.workspace,
            "capabilityAuthority": (
                "window-width fixture only; width does not infer device identity"
            ),
            "ready": True,
            "boundaries": [
                "not hinge sensor or posture semantics",
                "not physical foldable qualification",
                "not automatic production capability selection",
                "not native form-factor parity",
                "not production desktop shell integration",
                "not release candidate",
                "not V1.2 Stable promotion",
            ],
        }

        if self.args.evidence_file:
            path = Path(self.args.evidence_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(data, indent=2), flush=True)
        self.evidence_written = True
        return GLib.SOURCE_REMOVE


def main() -> int:
    args = parse_args()
    app = GlazeWindowAdaptationCandidate(args)
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    raise SystemExit(main())
