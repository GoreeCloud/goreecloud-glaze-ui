#!/usr/bin/env python3
"""Bounded GTK4 Personalization + Living Frosted adapter reference for GLAZE UI V1.2 Candidate.

The reference reads local system appearance when Follow System is selected, accepts
only a caller-supplied RGB summary for wallpaper atmosphere, and owns no persistence,
synchronization, image acquisition, telemetry, network transport, release, or Stable
authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

WALLPAPER_ALPHA = 0.08
WALLPAPER_MAX_ALPHA = 0.12
WALLPAPER_CHROMA_RETENTION = 0.24
WALLPAPER_MAX_CHROMA_RETENTION = 0.28
MIN_TARGET_PX = 48
TOUCH_ASSISTANCE_PX = 56


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--appearance", default="follow-system")
    parser.add_argument("--clarity", default="balanced")
    parser.add_argument("--reduced-transparency", action="store_true")
    parser.add_argument("--touch-assistance", action="store_true")
    parser.add_argument("--wallpaper-r", type=int)
    parser.add_argument("--wallpaper-g", type=int)
    parser.add_argument("--wallpaper-b", type=int)
    parser.add_argument("--evidence-file")
    parser.add_argument("--auto-interact", action="store_true")
    return parser.parse_args()


def normalize_appearance(value: str | None) -> str:
    candidate = (value or "follow-system").strip().lower()
    if candidate in {"light", "dark", "deep-dark"}:
        return candidate
    return "follow-system"


def normalize_clarity(value: str | None) -> str:
    candidate = (value or "balanced").strip().lower()
    return candidate if candidate in {"clear", "balanced", "dense"} else "balanced"


def resolve_system_appearance() -> tuple[str, str]:
    source = Gio.SettingsSchemaSource.get_default()
    schema = source.lookup("org.gnome.desktop.interface", True) if source is not None else None
    if schema is not None and schema.has_key("color-scheme"):
        settings = Gio.Settings.new_full(schema, None, None)
        scheme = settings.get_string("color-scheme")
        return ("dark" if scheme in {"prefer-dark", "dark"} else "light", "org.gnome.desktop.interface/color-scheme")

    gtk_settings = Gtk.Settings.get_default()
    prefer_dark = bool(gtk_settings.get_property("gtk-application-prefer-dark-theme")) if gtk_settings is not None else False
    return ("dark" if prefer_dark else "light", "Gtk.Settings/gtk-application-prefer-dark-theme")


def resolve_appearance(preference: str) -> tuple[str, str]:
    if preference in {"light", "dark", "deep-dark"}:
        return preference, "manual"
    return resolve_system_appearance()


def valid_channel(value: int | None) -> bool:
    return isinstance(value, int) and 0 <= value <= 255


def derive_wallpaper_atmosphere(r: int | None, g: int | None, b: int | None) -> dict[str, object] | None:
    if not all(valid_channel(value) for value in (r, g, b)):
        return None
    assert r is not None and g is not None and b is not None
    luminance = round(r * 0.2126 + g * 0.7152 + b * 0.0722)
    channels = [
        max(0, min(255, round(luminance + (channel - luminance) * WALLPAPER_CHROMA_RETENTION)))
        for channel in (r, g, b)
    ]
    return {
        "rgb": channels,
        "alpha": WALLPAPER_ALPHA,
        "chromaRetention": WALLPAPER_CHROMA_RETENTION,
    }


def neutral_surface_channel(appearance: str, clarity: str) -> int:
    values = {
        "light": {"clear": 246, "balanced": 250, "dense": 254},
        "dark": {"clear": 36, "balanced": 42, "dense": 50},
        "deep-dark": {"clear": 27, "balanced": 31, "dense": 38},
    }
    return values[appearance][clarity]


def composite_atmosphere(neutral: int, atmosphere: dict[str, object] | None) -> tuple[int, int, int]:
    if atmosphere is None:
        return neutral, neutral, neutral
    rgb = atmosphere["rgb"]
    alpha = min(float(atmosphere["alpha"]), WALLPAPER_MAX_ALPHA)
    assert isinstance(rgb, list) and len(rgb) == 3
    return tuple(round(neutral * (1.0 - alpha) + int(channel) * alpha) for channel in rgb)


class PersonalizationCandidate(Gtk.Application):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(application_id="com.goreecloud.glazeui.reference.v12.personalization", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.args = args
        self.preference = normalize_appearance(args.appearance)
        self.clarity = normalize_clarity(args.clarity)
        self.resolved_appearance = "light"
        self.system_source = "unresolved"
        self.atmosphere: dict[str, object] | None = None
        self.window: Gtk.ApplicationWindow | None = None
        self.action: Gtk.Button | None = None
        self.status: Gtk.Label | None = None
        self.sample: Gtk.Box | None = None
        self.evidence_written = False

    def do_activate(self) -> None:
        if self.window is not None:
            self.window.present()
            return

        self.resolved_appearance, self.system_source = resolve_appearance(self.preference)
        derived = derive_wallpaper_atmosphere(self.args.wallpaper_r, self.args.wallpaper_g, self.args.wallpaper_b)
        self.atmosphere = None if self.args.reduced_transparency else derived
        self._install_css()
        self.window = self._build_window()
        self.window.present()
        GLib.timeout_add(250, self._after_present)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        neutral = neutral_surface_channel(self.resolved_appearance, self.clarity)
        surface = composite_atmosphere(neutral, self.atmosphere)
        if self.resolved_appearance == "light":
            canvas, text, secondary, line = (239, 242, 246), (25, 25, 28), (92, 92, 99), (205, 208, 214)
        elif self.resolved_appearance == "deep-dark":
            canvas, text, secondary, line = (8, 8, 10), (247, 247, 248), (188, 188, 194), (74, 74, 80)
        else:
            canvas, text, secondary, line = (18, 18, 20), (247, 247, 248), (188, 188, 194), (76, 76, 82)
        target = TOUCH_ASSISTANCE_PX if self.args.touch_assistance else MIN_TARGET_PX
        css = f"""
window.personalization-shell {{ background: rgb({canvas[0]}, {canvas[1]}, {canvas[2]}); color: rgb({text[0]}, {text[1]}, {text[2]}); }}
.personalization-card, .personalization-sample {{ border: 1px solid rgb({line[0]}, {line[1]}, {line[2]}); border-radius: 26px; padding: 18px; }}
.personalization-card {{ background: rgb({neutral}, {neutral}, {neutral}); }}
.personalization-sample {{ background: rgb({surface[0]}, {surface[1]}, {surface[2]}); }}
.personalization-secondary {{ color: rgb({secondary[0]}, {secondary[1]}, {secondary[2]}); }}
.personalization-title {{ font-size: 28px; font-weight: 800; }}
.personalization-section {{ font-size: 19px; font-weight: 700; }}
button.personalization-action {{ min-height: {target}px; border-radius: 999px; padding: 8px 18px; background: rgb(82, 151, 181); color: white; font-weight: 700; }}
button.personalization-action:focus {{ outline: 2px solid rgb(82, 151, 181); outline-offset: 2px; }}
"""
        provider.load_from_data(css.encode("utf-8"))
        display = self.get_active_window().get_display() if self.get_active_window() is not None else None
        if display is None:
            from gi.repository import Gdk  # noqa: PLC0415
            display = Gdk.Display.get_default()
        if display is None:
            raise RuntimeError("GTK display unavailable")
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_window(self) -> Gtk.ApplicationWindow:
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("GLAZE UI V1.2 — Personalization Native Adapter Candidate")
        window.set_default_size(760, 680)
        window.set_size_request(620, 560)
        window.add_css_class("personalization-shell")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        window.set_child(scroll)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_top(24)
        page.set_margin_bottom(28)
        page.set_margin_start(24)
        page.set_margin_end(24)
        scroll.set_child(page)

        title = Gtk.Label(label="Native Personalization adapter", xalign=0)
        title.add_css_class("personalization-title")
        title.set_wrap(True)
        page.append(title)

        intro = Gtk.Label(
            label="Follow System, Living Frosted Clarity, and bounded wallpaper atmosphere remain local adapter behavior. Neutral structure and semantic meaning stay authoritative.",
            xalign=0,
        )
        intro.add_css_class("personalization-secondary")
        intro.set_wrap(True)
        page.append(intro)

        facts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        facts.add_css_class("personalization-card")
        values = [
            ("Appearance preference", "Follow System" if self.preference == "follow-system" else self.preference.replace("-", " ").title()),
            ("Resolved appearance", self.resolved_appearance.replace("-", " ").title()),
            ("System source", self.system_source),
            ("Clarity", self.clarity.title()),
            ("Reduced Transparency", "Enabled" if self.args.reduced_transparency else "Disabled"),
            ("Target floor", f"{TOUCH_ASSISTANCE_PX if self.args.touch_assistance else MIN_TARGET_PX} px"),
            ("Wallpaper atmosphere", "Local bounded RGB summary" if self.atmosphere is not None else "None"),
        ]
        for name, value in values:
            row = Gtk.Label(label=f"{name}: {value}", xalign=0)
            row.set_wrap(True)
            facts.append(row)
        page.append(facts)

        self.sample = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.sample.add_css_class("personalization-sample")
        sample_title = Gtk.Label(label="Living Frosted", xalign=0)
        sample_title.add_css_class("personalization-section")
        self.sample.append(sample_title)
        sample_body = Gtk.Label(
            label=(
                "Reduced Transparency suppresses decorative atmosphere while preserving structure and content."
                if self.args.reduced_transparency
                else "Clarity changes optical expression; a bounded local atmosphere may decorate but never replace the neutral material authority."
            ),
            xalign=0,
        )
        sample_body.add_css_class("personalization-secondary")
        sample_body.set_wrap(True)
        self.sample.append(sample_body)
        page.append(self.sample)

        self.status = Gtk.Label(label="Action: Ready", xalign=0)
        self.status.add_css_class("personalization-secondary")
        page.append(self.status)

        self.action = Gtk.Button(label="Personalization action")
        self.action.add_css_class("personalization-action")
        self.action.set_can_focus(True)
        self.action.connect("clicked", self._on_action)
        page.append(self.action)

        boundary = Gtk.Label(
            label="Candidate boundary: headless GTK adapter evidence is not physical-display, compositor, assistive-technology, persistence, cross-device sync, production, Release Candidate, or Stable acceptance.",
            xalign=0,
        )
        boundary.add_css_class("personalization-secondary")
        boundary.set_wrap(True)
        page.append(boundary)
        return window

    def _on_action(self, _button: Gtk.Button) -> None:
        assert self.status is not None
        self.status.set_label("Action: Complete")

    def _after_present(self) -> bool:
        if self.args.auto_interact and self.action is not None:
            self.action.emit("clicked")
        GLib.timeout_add(250, self._emit_evidence)
        return GLib.SOURCE_REMOVE

    def _emit_evidence(self) -> bool:
        if self.evidence_written:
            return GLib.SOURCE_REMOVE
        assert self.window is not None and self.action is not None and self.status is not None and self.sample is not None
        neutral = neutral_surface_channel(self.resolved_appearance, self.clarity)
        surface = composite_atmosphere(neutral, self.atmosphere)
        data = {
            "schemaVersion": 1,
            "product": "GLAZE UI V1.2 Personalization Linux adapter reference",
            "lifecycle": "Candidate native evidence",
            "platform": "Linux GTK4",
            "gtkVersion": f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
            "appearancePreference": self.preference,
            "resolvedAppearance": self.resolved_appearance,
            "systemAppearanceSource": self.system_source,
            "clarity": self.clarity,
            "reducedTransparency": bool(self.args.reduced_transparency),
            "touchAssistance": bool(self.args.touch_assistance),
            "wallpaperAtmosphere": self.atmosphere,
            "neutralSurfaceRgb": [neutral, neutral, neutral],
            "compositedSurfaceRgb": list(surface),
            "targetHeightPx": self.action.get_allocated_height(),
            "sampleHeightPx": self.sample.get_allocated_height(),
            "window": {"width": self.window.get_width(), "height": self.window.get_height()},
            "interactionState": self.status.get_label(),
            "ready": True,
            "boundaries": [
                "not compositor-wide Wayland backdrop blur fidelity",
                "not physical-display qualification",
                "not assistive-technology acceptance",
                "not consumer persistence ownership",
                "not wallpaper-source acquisition",
                "not cross-device synchronization",
                "not production acceptance",
                "not Release Candidate acceptance",
                "not V1.2 Stable promotion",
            ],
        }
        if self.args.evidence_file:
            path = Path(self.args.evidence_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.evidence_written = True
        return GLib.SOURCE_REMOVE


def main() -> int:
    args = parse_args()
    app = PersonalizationCandidate(args)
    return int(app.run(None))


if __name__ == "__main__":
    raise SystemExit(main())
