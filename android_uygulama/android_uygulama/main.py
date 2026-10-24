"""
YouTube Indirici - Android (Kivy + yt-dlp)
Videolar telefonda  Download/YouTubeIndirici  klasorune kaydedilir.
"""
import os
import threading

try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform

import yt_dlp

Window.softinput_mode = "below_target"

FORMATS = {
    "Video (MP4, en iyi hazır kalite)": "best[ext=mp4]/best",
    "Video (MP4, en fazla 720p)": "best[ext=mp4][height<=720]/best[height<=720]/best",
    "Sadece ses (M4A)": "bestaudio[ext=m4a]/bestaudio",
}


def ask_permissions():
    if platform != "android":
        return
    try:
        from android.permissions import Permission, request_permissions

        request_permissions(
            [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
        )
    except Exception:
        pass


def get_save_dir(app):
    if platform == "android":
        try:
            from android.storage import primary_external_storage_path

            base = os.path.join(primary_external_storage_path(), "Download")
        except Exception:
            base = "/storage/emulated/0/Download"
    else:
        base = os.path.join(os.path.expanduser("~"), "Downloads")
    path = os.path.join(base, "YouTubeIndirici")
    try:
        os.makedirs(path, exist_ok=True)
        # yazilabiliyor mu test et
        test = os.path.join(path, ".test")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        return path
    except Exception:
        return app.user_data_dir


class Root(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(16), spacing=dp(10), **kw)

        self.add_widget(
            Label(text="YouTube İndirici", font_size="22sp", size_hint_y=None, height=dp(48))
        )

        self.url = TextInput(
            hint_text="Video linkini buraya yapıştır",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
        )
        self.add_widget(self.url)

        paste = Button(text="Yapıştır", size_hint_y=None, height=dp(48))
        paste.bind(on_release=self.paste)
        self.add_widget(paste)

        self.fmt = Spinner(
            text=list(FORMATS)[0],
            values=list(FORMATS),
            size_hint_y=None,
            height=dp(48),
        )
        self.add_widget(self.fmt)

        self.btn = Button(text="İNDİR", size_hint_y=None, height=dp(56), font_size="18sp")
        self.btn.bind(on_release=self.start)
        self.add_widget(self.btn)

        self.bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(20))
        self.add_widget(self.bar)

        self.status = Label(
            text="Linki yapıştırıp İNDİR'e bas.\nVideolar: Download/YouTubeIndirici",
            halign="left",
            valign="top",
        )
        self.status.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        self.add_widget(self.status)

    def paste(self, *_):
        try:
            self.url.text = (Clipboard.paste() or "").strip()
        except Exception:
            pass

    def set_status(self, text, progress=None):
        def _do(_dt):
            self.status.text = text
            if progress is not None:
                self.bar.value = progress

        Clock.schedule_once(_do)

    def start(self, *_):
        link = self.url.text.strip()
        if not link:
            self.set_status("Önce bir video linki yapıştır.")
            return
        self.btn.disabled = True
        self.bar.value = 0
        self.set_status("Başlıyor...")
        threading.Thread(target=self.download, args=(link,), daemon=True).start()

    def hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                pct = d["downloaded_bytes"] / total * 100
                speed = (d.get("_speed_str") or "").strip()
                self.set_status(f"İndiriliyor... %{pct:.1f}  {speed}", pct)
        elif d["status"] == "finished":
            self.set_status("Kaydediliyor...", 100)

    def download(self, link):
        app = App.get_running_app()
        outdir = get_save_dir(app)
        opts = {
            "format": FORMATS[self.fmt.text],
            "outtmpl": os.path.join(outdir, "%(title).80s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self.hook],
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([link])
            self.set_status(f"Tamamlandı!\nKaydedildiği yer:\n{outdir}", 100)
        except Exception as e:
            self.set_status(f"Hata oluştu:\n{str(e)[:300]}", 0)
        finally:
            Clock.schedule_once(lambda _dt: setattr(self.btn, "disabled", False))


class IndiriciApp(App):
    title = "YouTube İndirici"

    def build(self):
        return Root()

    def on_start(self):
        ask_permissions()


if __name__ == "__main__":
    IndiriciApp().run()
