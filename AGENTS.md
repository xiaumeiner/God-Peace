# God Peace Hub — инструкция для ИИ

Документ для другого AI/агента: где код, как собирать, что не ломать.

## Где исходники

**Корень проекта (локально):** `C:\Users\xiaumeiner\Projects\my-ai`

**God Peace (исходники):** `my-ai/hub/`

**GitHub (только hub/ в корне репо):** https://github.com/xiaumeiner/God-Peace

| Что | Путь |
|-----|------|
| Точка входа | `hub/run.py` |
| GUI, логика хаба | `hub/app.py` |
| Автообновление | `hub/updater.py` |
| Push на GitHub | `hub/push_github.ps1` |
| Пути, константы, env | `hub/config.py` |
| Сборка exe | `hub/build.ps1`, `hub/build_bundle.ps1`, `hub/god_peace.spec` |
| Готовый билд | `hub/dist/GodPeace/GodPeace.exe` |
| Ресурсы (иконки, GIF) | `hub/assets/` |
| Встроенные инструменты | `hub/bundled/` (Calamity, MapMark installer) |
| venv (локально) | `hub/.venv/` |
| Правило Cursor | `.cursor/rules/god-peace-hub.mdc` |

**Не править как исходники:** `hub/dist/`, `hub/build/`, `hub/.venv/`

**Отдельный подпроект в том же репо:** `story/` — оригинальная история «Луми», правила в `.cursor/rules/lumi-story.mdc`. К God Peace не относится.

---

## Структура модулей hub/

```
run.py              → entry, single-instance check
app.py              → главное окно CustomTkinter
config.py           → APP_NAME, пути, Majestic API из majestic.env
single_instance.py  → один процесс + IPC «показать окно»
tray_icon.py        → трей (закрытие = свернуть)
calamity_runner.py  → запуск Calamity (Safe/Gaming/Full)
mapmark_launcher.py → установка/запуск MapMark
extra_tweaks.py     → доп. твики из Desktop/2321
hub_state.py        → какие твики применены (откат)
system_status.py    → RAM, ADMIN, MAP, TWEAKED в UI
gif_banner.py       → XGOD GIF в шапке

majestic_api.py     → HTTP-клиент Majestic API
majestic_captures.py→ парсинг каптов, CaptEvent
family_registry.py  → семьи, аватарки, кэш логотипов
capt_watcher.py     → фоновый poll каждые 60s
capt_notifier.py    → звук + вызов popup
capt_popup.py       → уведомление справа снизу
```

---

## Сборка и запуск (обязательно после изменений)

```powershell
cd C:\Users\xiaumeiner\Projects\my-ai\hub
.\build.ps1
Start-Process .\dist\GodPeace\GodPeace.exe
```

- `build.ps1` сам вызывает `build_bundle.ps1`
- Не отдавать пользователю только `.py` — нужен рабочий `dist/GodPeace/`
- Перед сборкой закрыть старый процесс: `Get-Process GodPeace | Stop-Process -Force`

Dev-режим (без exe):

```powershell
cd hub
.\.venv\Scripts\python.exe run.py
```

---

## Конфигурация

Файл **`majestic.env`** рядом с exe (или в `hub/` при dev), **в git не коммитить**:

```env
MAJESTIC_API_KEY=...
MAJESTIC_SERVER_ID=RU18
MAJESTIC_FAMILY_NAME=Alarm
```

Discord XGOD: `config.py` → `DISCORD_XGOD_URL = https://discord.gg/PW9rSczR2W`

Данные runtime рядом с exe:

- `god_peace_state.json` — применённые твики
- `capt_watch_state.json` — seen IDs каптов
- `cache/family_logos/` — кэш аватарок семей

---

## Majestic API (капты)

- Base: `https://api.majestic-files.com`
- Headers: `X-API-KEY`, `X-LANGUAGE: ru`
- Лимит: **5 запросов / 60 сек** → poll раз в 60s (`MAJESTIC_POLL_SECONDS`)
- Endpoints:
  - `GET /v1/ext/family-wars/{server}` — активные/история каптов
  - `GET /v1/ext/captures/{server}` — зоны, теги, цвета семей
- Прямого URL логотипа в JSON нет — fallback: круг с буквой + цвет семьи

---

## UX-поведение (не ломать)

1. **Закрытие крестиком** → сворачивание в трей, капты продолжают мониториться
2. **Выход** → только из меню трея «Выход»
3. **Повторный запуск exe** → не новый процесс, а показ окна из трея (`single_instance.py`)
4. **Popup капта** → правый нижний угол, CTkImage (не ImageTk), без цветной обводки окна
5. **SideForge удалён** — не возвращать

---

## CustomTkinter — типичные ошибки

- **Не создавать `CTkFont` на уровне модуля** до `CTk()` — будет `RuntimeError: Too early to use font`. Ленивая инициализация (см. `capt_popup._font()`).
- Popup: `withdraw()` → layout → `geometry()` → `deiconify()`
- Картинки в CTk: `CTkImage`, хранить ссылки в `self._images`
- UI-поток: watcher/tray в threads, обновление GUI через `master.after(0, ...)`

---

## Цвета UI (God Peace dark)

```
BG=#0a0a0a  CARD=#141414  BORDER=#2a2a2a
TEXT=#f0f0f0  MUTED=#666666/#888888
DANGER=#c0392b  WARNING=#d4a017 (атака)
```

---

## Git / GitHub

- Репозиторий: `xiaumeiner/God-Peace` (public)
- Автообновление: Releases в том же репо, токен не нужен
- Push исходников: `.\hub\push_github.ps1`
- Публикация zip: `.\hub\publish_release.ps1 -Version X.Y.Z`
- Не коммитить `majestic.env`, `.venv/`, `dist/`, `build/`
- SideForge и связанные пути не восстанавливать

---

## Чеклист для агента

- [ ] Менял `hub/*.py` → запустил `build.ps1`
- [ ] Запустил `GodPeace.exe` после сборки
- [ ] Не трогал `dist/` как источник правды
- [ ] Новые модули добавил в `god_peace.spec` → `hiddenimports`
- [ ] Фоновые задачи не блокируют GUI
- [ ] API Majestic — не чаще лимита
- [ ] Single-instance и трей работают после изменений в `run.py` / `app.py`

---

## Контакты / ссылки

- Discord XGOD: https://discord.gg/PW9rSczR2W
- Автор: xiaumeiner (кнопка «Обратная связь» в приложении)
