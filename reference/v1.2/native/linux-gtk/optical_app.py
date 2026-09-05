#!/usr/bin/env python3
"""Bounded GTK4 V1.2 Frosted Optical reference; no compositor backdrop-blur claim."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import gi
gi.require_version("Gtk","4.0")
from gi.repository import Gdk,Gio,GLib,Gtk

ROOT=Path(__file__).resolve().parent
CSS=ROOT/"glaze-v1.2-linux-optical.css"

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--appearance",choices=("light","dark","deep-dark"),default="light")
    p.add_argument("--performance-profile",choices=("full","reduced","minimal"),default="full")
    p.add_argument("--reduced-transparency",action="store_true")
    p.add_argument("--touch-assistance",action="store_true")
    p.add_argument("--large-text",action="store_true")
    p.add_argument("--evidence-file");p.add_argument("--auto-interact",action="store_true")
    return p.parse_args()

class App(Gtk.Application):
    def __init__(self,a):
        super().__init__(application_id="com.goreecloud.glazeui.reference.v12.optical",flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.a=a;self.win=None;self.action=None;self.state=None;self.search=None;self.tiles=[]
    def do_activate(self):
        provider=Gtk.CssProvider();provider.load_from_path(str(CSS))
        display=Gdk.Display.get_default()
        if display is None:raise RuntimeError("GTK display unavailable")
        Gtk.StyleContext.add_provider_for_display(display,provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        w=Gtk.ApplicationWindow(application=self);self.win=w;w.set_title("GLAZE UI V1.2 Frosted Optical Candidate");w.set_default_size(1040,780)
        w.add_css_class("optical-shell");w.add_css_class(self.a.appearance);w.add_css_class("profile-"+self.a.performance_profile)
        if self.a.reduced_transparency:w.add_css_class("reduced-transparency")
        if self.a.touch_assistance:w.add_css_class("touch-assistance")
        if self.a.large_text:w.add_css_class("large-text")
        scroll=Gtk.ScrolledWindow();w.set_child(scroll)
        page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14);page.set_margin_top(20);page.set_margin_bottom(24);page.set_margin_start(20);page.set_margin_end(20);scroll.set_child(page)
        page.append(self.card("GLAZE UI V1.2 CANDIDATE\nFrost White is the material.\nWhite behaves as light. Ice Blue behaves as atmosphere.","glass"))
        mode="Opaque Frost" if self.a.reduced_transparency or self.a.performance_profile=="minimal" else "Frost White"
        page.append(self.card(f"Appearance · {self.a.appearance}\nPerformance · {self.a.performance_profile.title()}\nMaterial · {mode}\nPrimary material: Frost White\nPrimary atmosphere: Ice Blue\nLegacy teal/amber atmosphere: retired","glass"))
        self.search=Gtk.SearchEntry();self.search.set_placeholder_text("Universal Search · Clear Frost");self.search.add_css_class("clear-frost");page.append(self.search)
        panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);panel.add_css_class("dense-frost")
        panel.append(Gtk.Label(label="Quick Settings · Dense Frost",xalign=0))
        for name in ("Wi-Fi · Connected","Performance · "+self.a.performance_profile.title()):
            b=Gtk.Button(label=name);b.add_css_class("setting-tile");b.add_css_class("active");self.tiles.append(b);panel.append(b)
        page.append(panel)
        critical=self.card("CRITICAL SYSTEM · OPAQUE FROST\nHigh-opacity clarity stays separate.","opaque-frost");page.append(critical)
        self.action=Gtk.Button(label="Primary action");self.action.add_css_class("primary-action");self.action.connect("clicked",self.clicked);page.append(self.action)
        self.state=Gtk.Label(label="Action: Ready",xalign=0);page.append(self.state)
        page.append(Gtk.Label(label="Candidate boundary: GTK/Xvfb optical roles only; not Wayland blur, physical display/GPU, AT, production, RC, or Stable acceptance.",xalign=0,wrap=True))
        w.present();GLib.timeout_add(250,self.after)
    def card(self,text,klass):
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);box.add_css_class(klass);box.append(Gtk.Label(label=text,xalign=0,wrap=True));return box
    def clicked(self,_):
        self.state.set_label("Action: Complete")
    def after(self):
        if self.a.auto_interact:self.action.emit("clicked")
        GLib.timeout_add(250,self.evidence);return GLib.SOURCE_REMOVE
    def evidence(self):
        data={"schemaVersion":1,"product":"GLAZE UI V1.2 Frosted Optical","lifecycle":"Candidate native evidence","platform":"Linux GTK4",
          "gtkVersion":f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}","appearance":self.a.appearance,
          "performanceProfile":self.a.performance_profile,"reducedTransparency":self.a.reduced_transparency,"touchAssistance":self.a.touch_assistance,
          "largeText":self.a.large_text,"nativeBackdropBlurClaim":False,"opticalRoles":{"primaryMaterial":"Frost White","primaryAtmosphere":"Ice Blue"},
          "interactionState":self.state.get_label(),"targets":{"action":self.action.get_allocated_height(),"search":self.search.get_allocated_height(),
          "tiles":[b.get_allocated_height() for b in self.tiles]},"ready":True}
        if self.a.evidence_file:
            p=Path(self.a.evidence_file);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+"\n")
        else:print(json.dumps(data,indent=2),flush=True)
        return GLib.SOURCE_REMOVE
def main():return App(args()).run([sys.argv[0]])
if __name__=="__main__":raise SystemExit(main())
