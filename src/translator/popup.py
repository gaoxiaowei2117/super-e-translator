"""GTK4 popup window for displaying translation results.

The window is positioned by the Wayland compositor; we cannot place it
at the cursor. Original text shown dim above, translation bold below.
Esc closes the window. Translation label is selectable (Ctrl+C to copy)
and a Copy button is provided as a fallback.
"""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402


def show(original: str, translation: str, truncated: bool = False) -> None:
    app = Gtk.Application(application_id="com.xgao.translator")

    def on_activate(application: Gtk.Application) -> None:
        win = Gtk.ApplicationWindow(application=application, title="Translator")
        win.set_default_size(480, 240)

        outer = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        if truncated:
            badge = Gtk.Label(label="⚠ 已截断到 2000 字符", xalign=0)
            badge.add_css_class("dim-label")
            outer.append(badge)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        orig_label = Gtk.Label(label=original, xalign=0, wrap=True, selectable=True)
        orig_label.add_css_class("dim-label")
        inner.append(orig_label)

        trans_label = Gtk.Label(
            label=translation, xalign=0, wrap=True, selectable=True
        )
        trans_label.add_css_class("title-3")
        inner.append(trans_label)

        scrolled.set_child(inner)
        outer.append(scrolled)

        def on_copy(_btn: Gtk.Button) -> None:
            display = Gdk.Display.get_default()
            if display is not None:
                display.get_clipboard().set(translation)

        copy_btn = Gtk.Button(label="复制译文")
        copy_btn.connect("clicked", on_copy)
        outer.append(copy_btn)

        controller = Gtk.EventControllerKey()

        def on_key(_ctrl, keyval, _keycode, _state) -> bool:
            if keyval == Gdk.KEY_Escape:
                win.close()
                return True
            return False

        controller.connect("key-pressed", on_key)
        win.add_controller(controller)

        win.set_child(outer)
        win.present()

    app.connect("activate", on_activate)
    app.run([])
