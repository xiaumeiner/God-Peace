# God Peace

Лаунчер для Majestic RP: Calamity-твики, MapMark, уведомления каптов, Discord XGOD.

## Сборка

```powershell
cd hub
.\build.ps1
```

Готовый exe: `dist/GodPeace/GodPeace.exe`

## Конфиг

Скопируй `majestic.env.example` → `majestic.env` рядом с exe:

- `MAJESTIC_API_KEY` — ключ Majestic API
- `GITHUB_TOKEN` — для автообновления из **private** GitHub Releases

## Релиз / автообновление

1. Поднять `APP_VERSION` в `config.py`
2. `.\build.ps1`
3. Zip папки `dist/GodPeace/` → `GodPeace-vX.Y.Z.zip`
4. GitHub → Releases → tag `vX.Y.Z`, прикрепить zip

Private repo: без `GITHUB_TOKEN` в `majestic.env` кнопка обновления не увидит релиз.

## Push на GitHub (только hub/)

Из корня монорепо `my-ai`:

```powershell
.\hub\push_github.ps1
```
