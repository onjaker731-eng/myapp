[app]
title = YouTube Downloader
package.name = youtubedownloader
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# Залежності
requirements = python3==3.11.0,kivy==2.3.0,yt-dlp

# Орієнтація
orientation = portrait

# Android
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.arch = arm64-v8a

# Дозволи
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
