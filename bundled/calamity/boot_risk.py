"""Твики и расширенные настройки, которые могут помешать загрузке Windows."""

from __future__ import annotations

BOOT_RISK: dict[str, dict[str, str]] = {
    "bcd_timer": {
        "level": "critical",
        "symbol": "⛔",
        "short": "Может не включиться ПК",
        "why": (
            "Меняет параметры загрузчика (disabledynamictick, useplatformtick). "
            "На части материнских плат и ноутбуков после перезагрузки — чёрный экран, "
            "зависание на логотипе или цикл перезагрузок."
        ),
        "recovery": (
            "1) Безопасный режим: удерживай Shift → «Перезагрузка» → «Поиск и устранение неисправностей» "
            "→ «Доп. параметры» → «Параметры загрузки» → «Безопасный режим».\n"
            "2) В Calamity отключи этот твик или на «Главная» / «Инструменты» → «Экстренный откат BCD».\n"
            "3) Из консоли восстановления (cmd): "
            "bcdedit /deletevalue disabledynamictick & "
            "bcdedit /deletevalue useplatformtick & "
            "bcdedit /deletevalue useplatformclock"
        ),
    },
    "disable_cstates": {
        "level": "critical",
        "symbol": "⛔",
        "short": "Может не включиться ПК",
        "why": (
            "Отключает энергосберегающие состояния CPU (C-States). "
            "На ноутбуках и некоторых AMD/Intel конфигурациях ПК может зависнуть при включении "
            "или уйти в постоянную перезагрузку."
        ),
        "recovery": (
            "1) Безопасный режим → отключи твик в Calamity или «Экстренный откат».\n"
            "2) regedit (от админа): удали значения Cstates и PerfEnablePackageIdle в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Processor\\Power\n"
            "3) Точка восстановления Windows, если создавалась до оптимизации."
        ),
    },
    "distribute_timers": {
        "level": "critical",
        "symbol": "⛔",
        "short": "Может не включиться ПК",
        "why": (
            "Включает DistributeTimers в ядре Windows. Редко, но на отдельных системах "
            "вызывает нестабильность или сбой загрузки после перезагрузки."
        ),
        "recovery": (
            "1) Безопасный режим → отключи твик в Calamity.\n"
            "2) regedit: удали DistributeTimers в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel"
        ),
    },
    "core_parking": {
        "level": "warning",
        "symbol": "⚠",
        "short": "Редкий риск загрузки",
        "why": (
            "Запрещает «парковку» ядер CPU (все ядра всегда активны). "
            "Обычно загрузка проходит, но на слабых ноутбуках возможны зависания при старте."
        ),
        "recovery": (
            "Безопасный режим → отключи твик в Calamity. "
            "Или regedit: удали MinProcessors и MaxProcessors в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\..."
        ),
    },
    "disable_mpo": {
        "level": "warning",
        "symbol": "⚠",
        "short": "Ломает перенос окон между мониторами",
        "why": (
            "OverlayTestMode=5 отключает Multi-Plane Overlay в DWM. "
            "На системах с двумя и более мониторами окна часто «залипают» на одном экране — "
            "их нельзя перетащить мышью на второй монитор."
        ),
        "recovery": (
            "1) Calamity → «Инструменты» → «Восстановление» → «Исправить перенос окон / мониторы».\n"
            "2) Отключи твик «Отключить MPO» и нажми «Откатить».\n"
            "3) regedit (админ): удали OverlayTestMode в HKLM\\SOFTWARE\\Microsoft\\Windows\\Dwm, "
            "перезапусти explorer или перезагрузи ПК."
        ),
    },
    "monitor_latency": {
        "level": "warning",
        "symbol": "⚠",
        "short": "Может ломать multi-monitor",
        "why": (
            "MonitorLatencyTolerance=0 в DXGKrnl уменьшает задержку вывода, "
            "но на части конфигураций с несколькими мониторами ухудшает работу DWM."
        ),
        "recovery": (
            "1) «Исправить перенос окон / мониторы» в Calamity.\n"
            "2) Откати твик «Monitor latency».\n"
            "3) regedit: удали MonitorLatencyTolerance и MonitorRefreshLatencyTolerance в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Services\\DXGKrnl"
        ),
    },
    "nvidia_pstate": {
        "level": "warning",
        "symbol": "⚠",
        "short": "Редкий риск загрузки",
        "why": (
            "Фиксирует видеокарту NVIDIA в максимальном P-состоянии. "
            "Иногда после перезагрузки — чёрный экран до входа в систему (драйвер не успевает)."
        ),
        "recovery": (
            "Безопасный режим → отключи твик. "
            "regedit: удали DisableDynamicPstate в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-...}\\0000"
        ),
    },
}

ADVANCED_BOOT_RISK: dict[str, dict[str, str]] = {
    "tsx": {
        "level": "critical",
        "symbol": "⛔",
        "short": "Может не включиться ПК",
        "why": (
            "Отключает Intel TSX через bcdedit. На части процессоров Intel "
            "может вызвать сбой загрузки или нестабильность ядра."
        ),
        "recovery": (
            "Консоль восстановления: bcdedit /deletevalue {current} tsx\n"
            "Или «Экстренный откат BCD» в Calamity из безопасного режима."
        ),
    },
    "large_system_cache": {
        "level": "warning",
        "symbol": "⚠",
        "short": "Редкий риск загрузки",
        "why": (
            "Переключает LargeSystemCache — больше RAM под файловый кэш, меньше под приложения. "
            "На системах с малым объёмом RAM возможны проблемы при старте."
        ),
        "recovery": (
            "Безопасный режим → «Расширенные» → выключи LargeSystemCache. "
            "regedit: LargeSystemCache = 0 в "
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management"
        ),
    },
}


def get_boot_risk(tweak_id: str) -> dict[str, str] | None:
    return BOOT_RISK.get(tweak_id)


def get_boot_risk_level(tweak_id: str) -> str | None:
    info = BOOT_RISK.get(tweak_id)
    return info["level"] if info else None


def get_advanced_boot_risk(setting_id: str) -> dict[str, str] | None:
    return ADVANCED_BOOT_RISK.get(setting_id)


def boot_risk_badge(tweak_id: str) -> str | None:
    info = BOOT_RISK.get(tweak_id)
    if not info:
        return None
    return f"{info['symbol']} {info['short']}"


def boot_risk_recovery_line(tweak_id: str) -> str | None:
    info = BOOT_RISK.get(tweak_id)
    if not info:
        return None
    return f"{info['symbol']} {info['short']}. {info['why']} Откат: {info['recovery'].split(chr(10))[0]}"


def format_full_recovery(tweak_id: str) -> str:
    info = BOOT_RISK.get(tweak_id) or ADVANCED_BOOT_RISK.get(tweak_id)
    if not info:
        return ""
    return f"{info['symbol']} {info['short']}\n\n{info['why']}\n\nКак откатить:\n{info['recovery']}"


def list_critical_tweak_ids() -> list[str]:
    return [k for k, v in BOOT_RISK.items() if v["level"] == "critical"]


def emergency_boot_recovery() -> tuple[bool, str]:
    """Откат всех настроек с критическим риском загрузки (нужны права админа)."""
    from advanced import set_tsx_disabled
    from engine import revert_bcd_timer_tweaks, revert_disable_cstates, revert_distribute_timers

    parts: list[str] = []
    for label, fn in (
        ("BCD таймер", revert_bcd_timer_tweaks),
        ("C-States", revert_disable_cstates),
        ("DistributeTimers", revert_distribute_timers),
    ):
        ok, msg = fn()
        parts.append(f"[{label}] {'OK' if ok else 'ошибка'}: {msg}")

    ok, msg = set_tsx_disabled(False)
    parts.append(f"[TSX] {'OK' if ok else 'ошибка'}: {msg}")
    parts.append("\nПерезагрузи ПК после отката.")

    return True, "\n".join(parts)


RECOVERY_GUIDE = """Если Windows не загружается после оптимизации:

1. Точка восстановления — если успел создать в Calamity до применения.
2. Безопасный режим — Shift + «Перезагрузка» → Поиск неисправностей → Доп. параметры → Параметры загрузки → Безопасный режим с сетью.
3. В Calamity: «Инструменты» → «Восстановление» → «Экстренный откат BCD и загрузки».
4. Консоль восстановления Windows (cmd от установочной флешки):
   bcdedit /deletevalue disabledynamictick
   bcdedit /deletevalue useplatformtick
   bcdedit /deletevalue useplatformclock
   bcdedit /deletevalue {current} tsx

⛔ — высокий риск: ПК может не включиться после перезагрузки.
⚠ — редкий риск: обычно загружается, но на слабом железе возможны проблемы."""
