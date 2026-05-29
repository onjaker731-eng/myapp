#!/usr/bin/env python3
"""
YouTube Video & Shorts Downloader — Kivy GUI Version
"""

import threading
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    raise SystemExit("❌ Встановіть yt-dlp: pip install yt-dlp")

# ── Kivy ────────────────────────────────────────────────────────────────────
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

# ── Налаштування вікна ───────────────────────────────────────────────────────
Window.size = (700, 560)
Window.clearcolor = (0.07, 0.07, 0.10, 1)

# ── Конфігурація ─────────────────────────────────────────────────────────────
DEFAULT_DOWNLOAD_DIR = "downloads"
FFMPEG_AUDIO_OPTS = {
    "key": "FFmpegExtractAudio",
    "preferredcodec": "mp3",
    "preferredquality": "192",
}

# ── Кольори ───────────────────────────────────────────────────────────────────
CLR_BG        = (0.07, 0.07, 0.10, 1)
CLR_SURFACE   = (0.12, 0.12, 0.17, 1)
CLR_ACCENT    = (0.98, 0.27, 0.36, 1)   # яскраво-червоний
CLR_ACCENT2   = (0.20, 0.60, 1.00, 1)   # блакитний
CLR_TEXT      = (0.95, 0.95, 0.97, 1)
CLR_MUTED     = (0.50, 0.52, 0.58, 1)
CLR_SUCCESS   = (0.18, 0.80, 0.44, 1)
CLR_ERROR     = (0.98, 0.27, 0.36, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# Допоміжні UI-компоненти
# ═══════════════════════════════════════════════════════════════════════════════

class CardBox(BoxLayout):
    """BoxLayout з заокругленим фоном-картою."""

    def __init__(self, bg_color=CLR_SURFACE, radius=14, **kwargs):
        super().__init__(**kwargs)
        self._bg_color = bg_color
        self._radius = radius
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self._radius])


class AccentButton(Button):
    def __init__(self, accent=CLR_ACCENT, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", accent)
        kwargs.setdefault("color", CLR_TEXT)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("font_size", dp(14))
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(44))
        super().__init__(**kwargs)


class ModeToggle(ToggleButton):
    """Кнопка-перемикач з двома станами: відео / аудіо."""

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", CLR_SURFACE)
        kwargs.setdefault("color", CLR_MUTED)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("font_size", dp(13))
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(40))
        super().__init__(**kwargs)
        self.bind(state=self._on_state)

    def _on_state(self, _, state):
        if state == "down":
            self.background_color = CLR_ACCENT2
            self.color = CLR_TEXT
        else:
            self.background_color = CLR_SURFACE
            self.color = CLR_MUTED


# ═══════════════════════════════════════════════════════════════════════════════
# Логіка завантаження (без змін відносно оригіналу)
# ═══════════════════════════════════════════════════════════════════════════════

class YouTubeDownloader:
    def __init__(self, output_dir: str = DEFAULT_DOWNLOAD_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.out_template = str(self.output_dir / "%(title)s.%(ext)s")

    def get_video_info(self, url: str) -> dict | None:
        opts = {"quiet": True, "no_warnings": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                return {
                    "title":     info.get("title", "Unknown"),
                    "duration":  info.get("duration", 0),
                    "uploader":  info.get("uploader", "Unknown"),
                    "formats":   len(info.get("formats", [])),
                }
        except Exception:
            return None

    def build_opts(self, audio_only: bool, progress_hook) -> dict:
        opts = {
            "outtmpl":        self.out_template,
            "quiet":          True,
            "no_warnings":    True,
            "progress_hooks": [progress_hook],
        }
        if audio_only:
            opts.update({
                "format":         "bestaudio/best",
                "postprocessors": [FFMPEG_AUDIO_OPTS],
            })
        else:
            opts.update({
                "format":               "bestvideo+bestaudio/best",
                "merge_output_format":  "mp4",
            })
        return opts

    def download(self, url: str, audio_only: bool, progress_hook) -> tuple[bool, str]:
        opts = self.build_opts(audio_only, progress_hook)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info     = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return True, filename
        except Exception as e:
            return False, str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# Головний екран
# ═══════════════════════════════════════════════════════════════════════════════

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(18),
                         spacing=dp(12), **kwargs)
        self.downloader = YouTubeDownloader()
        self._build_ui()

    # ── Будуємо інтерфейс ─────────────────────────────────────────────────────

    def _build_ui(self):
        # Заголовок
        self.add_widget(Label(
            text="▶  YouTube Downloader",
            font_size=dp(22), bold=True,
            color=CLR_ACCENT,
            size_hint_y=None, height=dp(46),
            halign="left", valign="middle",
        ))

        # Поле URL
        url_card = CardBox(orientation="vertical",
                           padding=(dp(12), dp(8)), spacing=dp(6),
                           size_hint_y=None, height=dp(84))
        url_card.add_widget(Label(
            text="Посилання на відео", font_size=dp(11),
            color=CLR_MUTED, halign="left",
            size_hint_y=None, height=dp(18),
        ))
        self.url_input = TextInput(
            hint_text="https://youtube.com/watch?v=...",
            background_color=(0, 0, 0, 0),
            foreground_color=CLR_TEXT,
            hint_text_color=(*CLR_MUTED[:3], 0.6),
            cursor_color=CLR_ACCENT2,
            font_size=dp(13),
            multiline=False,
            size_hint_y=None, height=dp(36),
        )
        url_card.add_widget(self.url_input)
        self.add_widget(url_card)

        # Перемикач режиму
        mode_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.btn_video = ModeToggle(text="🎥  Відео (MP4)", group="mode",
                                    state="down")
        self.btn_audio = ModeToggle(text="🔊  Аудіо (MP3)", group="mode")
        mode_row.add_widget(self.btn_video)
        mode_row.add_widget(self.btn_audio)
        self.add_widget(mode_row)

        # Кнопки дій
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.btn_info     = AccentButton(text="ℹ  Інфо",    accent=CLR_SURFACE)
        self.btn_download = AccentButton(text="⬇  Завантажити", accent=CLR_ACCENT)
        btn_row.add_widget(self.btn_info)
        btn_row.add_widget(self.btn_download)
        self.add_widget(btn_row)

        self.btn_info.bind(on_press=self._on_info)
        self.btn_download.bind(on_press=self._on_download)

        # Прогрес-бар
        self.progress = ProgressBar(max=100, value=0,
                                    size_hint_y=None, height=dp(6))
        self.add_widget(self.progress)

        # Статус-рядок
        self.status_label = Label(
            text="Готовий до роботи",
            font_size=dp(12), color=CLR_MUTED,
            size_hint_y=None, height=dp(22),
            halign="left", valign="middle",
        )
        self.add_widget(self.status_label)

        # Лог
        log_card = CardBox(orientation="vertical",
                           padding=(dp(12), dp(8)))
        log_card.add_widget(Label(
            text="Журнал", font_size=dp(11),
            color=CLR_MUTED, halign="left",
            size_hint_y=None, height=dp(20),
        ))
        scroll = ScrollView()
        self.log_label = Label(
            text="",
            font_size=dp(12), color=CLR_TEXT,
            halign="left", valign="top",
            markup=True,
            size_hint_y=None,
        )
        self.log_label.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
        scroll.add_widget(self.log_label)
        log_card.add_widget(scroll)
        self.add_widget(log_card)

    # ── Хелпери ───────────────────────────────────────────────────────────────

    def _log(self, text: str, color: tuple = CLR_TEXT):
        hex_c = "#{:02x}{:02x}{:02x}".format(
            int(color[0]*255), int(color[1]*255), int(color[2]*255))
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[color={hex_c}][{ts}] {text}[/color]\n"
        Clock.schedule_once(lambda dt: self._append_log(line))

    def _append_log(self, line: str):
        self.log_label.text += line

    def _set_status(self, text: str, color=CLR_MUTED):
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", text))
        Clock.schedule_once(lambda dt: setattr(self.status_label, "color", color))

    def _set_progress(self, value: float):
        Clock.schedule_once(lambda dt: setattr(self.progress, "value", value))

    def _set_buttons(self, enabled: bool):
        def _do(dt):
            self.btn_download.disabled = not enabled
            self.btn_info.disabled     = not enabled
        Clock.schedule_once(_do)

    def _get_url(self) -> str | None:
        url = self.url_input.text.strip()
        if not url:
            self._log("⚠ Введіть посилання!", CLR_ACCENT)
            return None
        return url

    # ── Інфо про відео ────────────────────────────────────────────────────────

    def _on_info(self, _):
        url = self._get_url()
        if not url:
            return
        self._set_buttons(False)
        self._log("🔍 Отримуємо інформацію...")
        threading.Thread(target=self._fetch_info, args=(url,), daemon=True).start()

    def _fetch_info(self, url: str):
        info = self.downloader.get_video_info(url)
        if not info:
            self._log("❌ Не вдалося отримати інформацію.", CLR_ERROR)
        else:
            m, s = divmod(info["duration"], 60)
            self._log(f"📹 [b]{info['title']}[/b]", CLR_TEXT)
            self._log(f"⏱  Тривалість: {m}:{s:02d}")
            self._log(f"👤 Канал: {info['uploader']}")
            self._log(f"📊 Форматів: {info['formats']}", CLR_ACCENT2)
        self._set_buttons(True)

    # ── Завантаження ──────────────────────────────────────────────────────────

    def _on_download(self, _):
        url = self._get_url()
        if not url:
            return
        audio_only = self.btn_audio.state == "down"
        self._set_buttons(False)
        self._set_progress(0)
        mode_str = "аудіо (MP3)" if audio_only else "відео (MP4)"
        self._log(f"⬇ Завантаження: {mode_str}")
        threading.Thread(
            target=self._run_download,
            args=(url, audio_only),
            daemon=True,
        ).start()

    def _run_download(self, url: str, audio_only: bool):
        ok, result = self.downloader.download(url, audio_only, self._progress_hook)
        if ok:
            self._log(f"✅ Збережено: {result}", CLR_SUCCESS)
            self._set_status("✅ Завершено!", CLR_SUCCESS)
            self._set_progress(100)
        else:
            self._log(f"❌ Помилка: {result}", CLR_ERROR)
            self._set_status("❌ Помилка завантаження", CLR_ERROR)
        self._set_buttons(True)

    def _progress_hook(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(pct_str)
                self._set_progress(pct)
            except ValueError:
                pass
            speed = d.get("_speed_str", "—")
            eta   = d.get("_eta_str", "—")
            self._set_status(f"⬇  {pct_str}%  |  {speed}  |  ETA: {eta}")
        elif status == "finished":
            self._set_status("⚙  Обробка файлу...")


# ═══════════════════════════════════════════════════════════════════════════════
# Додаток
# ═══════════════════════════════════════════════════════════════════════════════

class YouTubeDownloaderApp(App):
    def build(self):
        self.title = "YouTube Downloader"
        return MainScreen()


if __name__ == "__main__":
    YouTubeDownloaderApp().run()