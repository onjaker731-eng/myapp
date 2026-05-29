[app]
title = YouTube Downloader
package.name = youtubedownloader
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# Залежності — без явної версії python3, p4a сам узгодить пару hostpython3/python3
# Але фіксуємо через p4a_python_version щоб гарантовано взяти 3.11
requirements = python3,kivy==2.3.0,yt-dlp

# Примусово 3.11 для p4a
p4a.python_version = 3.11

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
