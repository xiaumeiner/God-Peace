"""Очистка диска — обычная и глубокая."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

NORMAL_CLEANUP_DESCRIPTION = """Обычная очистка — безопасно для ежедневного использования:

• Временные файлы Windows и браузеров
• Корзина
• Кэш миниатюр и шейдеров DirectX
• Сброс DNS-кэша
• Старые файлы Prefetch (Windows создаст новые)

Не трогаем: игры, документы, сохранения, установленные программы."""

DEEP_CLEANUP_DESCRIPTION = """Глубокая очистка — только если понимаете последствия:

Всё из обычной, плюс:

• Кэш обновлений Windows (может заново скачать патчи)
• Журналы событий (историю ошибок не восстановить)
• Папка Windows.old после апгрейда системы
• Очистка компонентов Windows (DISM, до ~3 минут)

⚠ Перед глубокой очисткой создайте точку восстановления.
⚠ Не удаляет игры и личные файлы."""


def _run_ps(script: str, timeout: int = 120) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=timeout,
        )
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, f"Таймаут ({timeout} с)"
    except Exception as exc:
        return False, str(exc)


def _clear_dir_files(path: Path, errors: list[str]) -> int:
    removed = 0
    if not path.exists():
        return 0
    try:
        for item in path.iterdir():
            try:
                if item.is_file():
                    item.unlink(missing_ok=True)
                    removed += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    removed += 1
            except OSError as exc:
                errors.append(f"{item.name}: {exc}")
    except OSError as exc:
        errors.append(f"{path}: {exc}")
    return removed


def _empty_recycle_bin() -> tuple[bool, str]:
    return _run_ps(
        r"Clear-RecycleBin -Force -ErrorAction SilentlyContinue; 'Recycle bin cleared'"
    )


def _flush_dns() -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True, (r.stdout or "").strip()
    except Exception as exc:
        return False, str(exc)


def run_normal_cleanup() -> tuple[bool, str, list[str]]:
    log: list[str] = []
    errors: list[str] = []
    total = 0

    temp_paths = [
        Path(os.environ.get("TEMP", r"C:\Windows\Temp")),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
        Path(r"C:\Windows\Temp"),
    ]
    for tp in temp_paths:
        if tp and str(tp) != ".":
            n = _clear_dir_files(tp, errors)
            total += n
            log.append(f"Temp {tp}: ~{n} объектов")

    local = Path(os.environ.get("LOCALAPPDATA", ""))
    thumb_dir = local / "Microsoft" / "Windows" / "Explorer"
    if thumb_dir.exists():
        thumbs = sum(1 for f in thumb_dir.glob("thumbcache_*.db") if f.unlink(missing_ok=True) is None)
        total += thumbs
        log.append(f"Миниатюры: {thumbs} файлов")

    dx_cache = local / "D3DSCache"
    if dx_cache.exists():
        n = _clear_dir_files(dx_cache, errors)
        total += n
        log.append(f"D3D Shader Cache: ~{n}")

    prefetch = Path(r"C:\Windows\Prefetch")
    if prefetch.exists():
        pf = 0
        for f in prefetch.glob("*.pf"):
            try:
                f.unlink()
                pf += 1
            except OSError:
                pass
        total += pf
        log.append(f"Prefetch: {pf} файлов")

    ok_rb, msg_rb = _empty_recycle_bin()
    log.append("Корзина: " + ("очищена" if ok_rb else msg_rb))

    ok_dns, msg_dns = _flush_dns()
    log.append("DNS: " + ("сброшен" if ok_dns else msg_dns))

    if errors:
        log.append(f"Предупреждений: {len(errors)} (файлы заняты системой)")

    summary = f"Обычная очистка завершена. Обработано ~{total} объектов."
    return True, summary, log


def run_deep_cleanup() -> tuple[bool, str, list[str]]:
    ok, summary, log = run_normal_cleanup()

    errors: list[str] = []

    do_cache = Path(r"C:\ProgramData\Microsoft\Windows\DeliveryOptimization\Cache")
    if do_cache.exists():
        n = _clear_dir_files(do_cache, errors)
        log.append(f"Delivery Optimization cache: ~{n}")

    wu_download = Path(r"C:\Windows\SoftwareDistribution\Download")
    if wu_download.exists():
        n = _clear_dir_files(wu_download, errors)
        log.append(f"WU Download cache: ~{n} (может потребоваться перезапуск WU)")

    wins_old = Path(r"C:\Windows.old")
    if wins_old.exists():
        log.append("Windows.old найден — удаление через takeown/rmdir...")
        ok_old, msg_old = _run_ps(
            rf"""
$path = 'C:\Windows.old'
if (Test-Path $path) {{
    takeown /f $path /r /d y 2>$null | Out-Null
    icacls $path /grant administrators:F /t 2>$null | Out-Null
    Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $path) {{ 'Windows.old частично занят — удалите вручную' }} else {{ 'Windows.old удалён' }}
}}
"""
        )
        log.append(msg_old or ("Windows.old: " + ("OK" if ok_old else "ошибка")))

    ok_ev, msg_ev = _run_ps(
        r"""
$logs = 'Application','System','Security','Microsoft-Windows-Windows Defender/Operational'
foreach ($l in $logs) { try { wevtutil cl $l 2>$null } catch {} }
'Event logs cleared'
"""
    )
    log.append("Журналы: " + (msg_ev if ok_ev else "частично"))

    win_logs = Path(r"C:\Windows\Logs")
    if win_logs.exists():
        n = 0
        for f in win_logs.rglob("*.log"):
            try:
                if f.stat().st_size > 0:
                    f.unlink()
                    n += 1
            except OSError:
                pass
        log.append(f"Windows\\Logs: {n} .log файлов")

    ok_dism, msg_dism = _run_ps(
        r"DISM /Online /Cleanup-Image /StartComponentCleanup 2>&1 | Out-String",
        timeout=180,
    )
    log.append("DISM: " + ("выполнен" if ok_dism else "ошибка или нужен admin"))
    if msg_dism:
        log.append(msg_dism[:200])

    _run_ps(
        r"""
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*" -Force -ErrorAction SilentlyContinue
Start-Process explorer
'Icon cache reset'
"""
    )
    log.append("Кэш иконок: сброшен")

    deep_summary = summary + " | Глубокая очистка выполнена."
    if errors:
        log.append(f"Ошибок доступа: {len(errors)}")
    return ok, deep_summary, log
