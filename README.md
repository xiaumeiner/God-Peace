# God Peace

Лаунчер для Majestic RP: Calamity-твики, MapMark, уведомления каптов, Discord XGOD.

## Сборка

```powershell
.\build.ps1
```

Готовый exe: `dist/GodPeace/GodPeace.exe`

## Конфиг

Скопируй `majestic.env.example` → `majestic.env` рядом с exe (Majestic API).

## GitHub

Репо: https://github.com/xiaumeiner/God-Peace (public)

Автообновление качает **Releases** оттуда — токен пользователям не нужен.

### Push исходников

Из монорепо `my-ai`:

```powershell
.\hub\push_github.ps1
```

### Выпустить обновление

1. Поднять `APP_VERSION` в `config.py`
2. `.\publish_release.ps1 -Version 1.0.1`
3. God-Peace → **Releases** → New release → tag `v1.0.1` → прикрепить `dist/GodPeace-v1.0.1.zip`
