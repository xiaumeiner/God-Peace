"""Дополнительные твики (~30) из Atlas, Win11Debloat, Sophia, shoober420, форумов."""

from __future__ import annotations

from engine import HKCU, HKLM, _ps, _run, delete_value, ensure_key, set_dword, set_string


def apply_fast_startup_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", "HiberbootEnabled", 0)
    return True, "Fast Startup (Hiberboot) disabled"


def revert_fast_startup_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", "HiberbootEnabled")
    return True, "Fast Startup restored"


def apply_llmnr_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient", "EnableMulticast", 0)
    return True, "LLMNR / multicast DNS disabled"


def revert_llmnr_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient", "EnableMulticast")
    return True, "LLMNR restored"


def apply_netbios_off() -> tuple[bool, str]:
    script = r"""
Get-CimInstance Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' | ForEach-Object {
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Tcpip\Parameters\Interfaces\$($_.SettingID)"
    if (Test-Path $p) { Set-ItemProperty -Path $p -Name NetbiosOptions -Value 2 -Type DWord -ErrorAction SilentlyContinue }
}
'NetBIOS over TCP/IP disabled on adapters'
"""
    return _ps(script)


def revert_netbios_on() -> tuple[bool, str]:
    return True, "NetBIOS: установите в свойствах сетевого адаптера вручную"


def apply_sticky_keys_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Control Panel\Accessibility\StickyKeys", "Flags", 506)
    set_dword(HKCU, r"Control Panel\Accessibility\ToggleKeys", "Flags", 58)
    set_dword(HKCU, r"Control Panel\Accessibility\Keyboard Response", "Flags", 122)
    return True, "Sticky/Toggle/Filter keys shortcuts disabled"


def revert_sticky_keys_on() -> tuple[bool, str]:
    for sub, val in (
        ("StickyKeys", 510),
        ("ToggleKeys", 62),
        ("Keyboard Response", 126),
    ):
        set_dword(HKCU, rf"Control Panel\Accessibility\{sub}", "Flags", val)
    return True, "Accessibility keys restored"


def apply_lock_screen_blur_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "DisableAcrylicBackgroundOnLogon", 1)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Lock Screen", "DisableLockScreenBlur", 1)
    return True, "Lock screen blur disabled"


def revert_lock_screen_blur_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "DisableAcrylicBackgroundOnLogon")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Lock Screen", "DisableLockScreenBlur")
    return True, "Lock screen blur restored"


def apply_activity_history_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "UploadUserActivities", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Privacy", "PublishUserActivities", 0)
    return True, "Activity History disabled"


def revert_activity_history_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "UploadUserActivities")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Privacy", "PublishUserActivities")
    return True, "Activity History restored"


def apply_storage_sense_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\StorageSense", "AllowStorageSenseGlobal", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy", "01", 0)
    return True, "Storage Sense disabled"


def revert_storage_sense_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\StorageSense", "AllowStorageSenseGlobal")
    return True, "Storage Sense policy removed"


def apply_remote_assistance_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Remote Assistance", "fAllowToGetHelp", 0)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Remote Assistance", "fAllowFullControl", 0)
    return True, "Remote Assistance disabled"


def revert_remote_assistance_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Remote Assistance", "fAllowToGetHelp", 1)
    return True, "Remote Assistance enabled"


def apply_pca_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisablePCA", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\PcaSvc", "Start", 4)
    return True, "Program Compatibility Assistant disabled"


def revert_pca_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisablePCA")
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\PcaSvc", "Start", 3)
    return True, "PCA restored"


def apply_onedrive_policy_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\OneDrive")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", 1)
    return True, "OneDrive sync policy disabled"


def revert_onedrive_policy_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC")
    return True, "OneDrive policy removed"


def apply_bluetooth_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\BTAGService", "Start", 4)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\bthserv", "Start", 4)
    _ps("Stop-Service BTAGService,bthserv -Force -ErrorAction SilentlyContinue")
    return True, "Bluetooth services disabled"


def revert_bluetooth_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\BTAGService", "Start", 3)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\bthserv", "Start", 3)
    return True, "Bluetooth services restored"


def apply_wlan_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WlanSvc", "Start", 4)
    _ps("Stop-Service WlanSvc -Force -ErrorAction SilentlyContinue")
    return True, "Wi-Fi service disabled (только если Ethernet)"


def revert_wlan_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WlanSvc", "Start", 2)
    return True, "Wi-Fi service restored"


def apply_ntfs_last_access_off() -> tuple[bool, str]:
    ok, msg = _run(["fsutil", "behavior", "set", "disablelastaccess", "1"])
    return ok, msg or "NTFS Last Access disabled"


def revert_ntfs_last_access_on() -> tuple[bool, str]:
    ok, msg = _run(["fsutil", "behavior", "set", "disablelastaccess", "2"])
    return ok, msg or "NTFS Last Access system managed"


def apply_web_search_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "CortanaConsent", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "DisableWebSearch", 1)
    return True, "Web search in taskbar disabled"


def revert_web_search_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "DisableWebSearch")
    return True, "Web search restored"


def apply_smartscreen_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 0)
    set_string(HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "SmartScreenEnabled", "Off")
    return True, "SmartScreen disabled — снижает безопасность"


def revert_smartscreen_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen")
    delete_value(HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "SmartScreenEnabled")
    return True, "SmartScreen restored"


def apply_maps_broker_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\MapsBroker", "Start", 4)
    return True, "MapsBroker disabled"


def revert_maps_broker_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\MapsBroker", "Start", 3)
    return True, "MapsBroker restored"


def apply_fax_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Fax", "Start", 4)
    return True, "Fax service disabled"


def revert_fax_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Fax", "Start", 3)
    return True, "Fax restored"


def apply_remote_registry_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\RemoteRegistry", "Start", 4)
    return True, "Remote Registry disabled"


def revert_remote_registry_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\RemoteRegistry", "Start", 3)
    return True, "Remote Registry restored"


def apply_consumer_features_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures", 1)
    return True, "Consumer features / suggested apps blocked"


def revert_consumer_features_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures")
    return True, "Consumer features policy removed"


def apply_chat_taskbar_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", 0)
    return True, "Chat icon hidden from taskbar"


def revert_chat_taskbar_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn")
    return True, "Chat taskbar restored"


def apply_snap_assist_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SnapAssist", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DITest", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableSnapAssistFlyout", 0)
    return True, "Snap Assist disabled"


def revert_snap_assist_on() -> tuple[bool, str]:
    for name in ("SnapAssist", "DITest", "EnableSnapAssistFlyout"):
        delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", name)
    return True, "Snap Assist restored"


def apply_transparency_blur_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\DWM", "ForceEffectMode", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", 0)
    return True, "Transparency / blur effects reduced"


def revert_transparency_blur_on() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1)
    delete_value(HKCU, r"Software\Microsoft\Windows\DWM", "ForceEffectMode")
    return True, "Transparency restored"


def apply_tcp_interface_nodelay() -> tuple[bool, str]:
    script = r"""
$n = 0
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' -ErrorAction SilentlyContinue |
    ForEach-Object {
        Set-ItemProperty -Path $_.PSPath -Name TcpAckFrequency -Value 1 -Type DWord -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $_.PSPath -Name TCPNoDelay -Value 1 -Type DWord -ErrorAction SilentlyContinue
        $n++
    }
"TCP NoDelay on $n interfaces"
"""
    return _ps(script)


def revert_tcp_interface_nodelay() -> tuple[bool, str]:
    script = r"""
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-ItemProperty -Path $_.PSPath -Name TcpAckFrequency -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $_.PSPath -Name TCPNoDelay -ErrorAction SilentlyContinue
    }
'TCP interface tweaks reverted'
"""
    return _ps(script)


def apply_large_system_cache_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "LargeSystemCache", 1)
    return True, "LargeSystemCache=1 (серверный профиль кэша)"


def revert_large_system_cache_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "LargeSystemCache", 0)
    return True, "LargeSystemCache=0"


def apply_spectre_meltdown_off() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "FeatureSettingsOverride", 3)
    set_dword(HKLM, mm, "FeatureSettingsOverrideMask", 3)
    return True, "Spectre/Meltdown mitigations OFF — перезагрузка. Высокий риск."


def revert_spectre_meltdown_on() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    delete_value(HKLM, mm, "FeatureSettingsOverride")
    delete_value(HKLM, mm, "FeatureSettingsOverrideMask")
    return True, "Spectre/Meltdown — дефолт (перезагрузка)"


def apply_tsx_off() -> tuple[bool, str]:
    ok, out = _run(["bcdedit", "/set", "{current}", "tsx", "off"])
    if not ok:
        return False, out or "TSX не поддерживается"
    return True, "TSX disabled — перезагрузка"


def revert_tsx_on() -> tuple[bool, str]:
    _run(["bcdedit", "/deletevalue", "{current}", "tsx"])
    return True, "TSX default"


def apply_svchost_ungroup() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB", 0)
    return True, "Svchost grouping disabled (threshold=0)"


def revert_svchost_ungroup() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB")
    return True, "Svchost grouping default"


def apply_edge_startup_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Edge")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled", 0)
    return True, "Edge startup boost / background off"


def revert_edge_startup_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled")
    return True, "Edge policies removed"


def apply_insider_service_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\wisvc", "Start", 4)
    return True, "Windows Insider service disabled"


def revert_insider_service_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\wisvc", "Start", 3)
    return True, "Insider service restored"


def apply_mouse_trails_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Control Panel\Mouse", "MouseTrails", 0)
    set_string(HKCU, r"Control Panel\Mouse", "MouseTrails", "0")
    return True, "Mouse trails disabled"


def revert_mouse_trails_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Control Panel\Mouse", "MouseTrails")
    return True, "Mouse trails restored"


def apply_gamebar_presence_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\GameBar", "ShowStartupPanel", 0)
    set_dword(HKCU, r"Software\Microsoft\GameBar", "UseNexusForGameBarEnabled", 0)
    set_dword(HKCU, r"System\GameConfigStore", "GameBarPresence", 0)
    return True, "Game Bar presence minimized"


def revert_gamebar_presence_on() -> tuple[bool, str]:
    delete_value(HKCU, r"System\GameConfigStore", "GameBarPresence")
    return True, "Game Bar presence restored"


def apply_hpet_platform_tick() -> tuple[bool, str]:
    ok1, o1 = _run(["bcdedit", "/set", "useplatformtick", "yes"])
    ok2, o2 = _run(["bcdedit", "/deletevalue", "useplatformclock"])
    return ok1, "\n".join(filter(None, [o1, o2])) or "Platform tick enabled"


def revert_hpet_platform_tick() -> tuple[bool, str]:
    _run(["bcdedit", "/deletevalue", "useplatformtick"])
    return True, "Platform tick reverted"


def apply_gamebar_policy_off() -> tuple[bool, str]:
    """Политика Windows: запрет Game DVR/записи — меньше оверхеда Xbox."""
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameDVR", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameRecording", 0)
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_Enabled", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)
    return True, "Game DVR policy disabled (Game Bar capture off)"


def revert_gamebar_policy_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameDVR")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameRecording")
    return True, "Game DVR policy removed"


def apply_visual_performance_max() -> tuple[bool, str]:
    """Классический «максимальная производительность» интерфейса Windows."""
    set_dword(HKCU, r"Control Panel\Desktop", "MenuShowDelay", 0)
    set_dword(HKCU, r"Control Panel\Desktop", "DragFullWindows", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewAlphaSelect", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAnimations", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)
    return True, "Visual effects: performance mode"


def revert_visual_performance_max() -> tuple[bool, str]:
    delete_value(HKCU, r"Control Panel\Desktop", "MenuShowDelay")
    delete_value(HKCU, r"Control Panel\Desktop", "DragFullWindows")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewAlphaSelect")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting")
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1)
    return True, "Visual effects restored"


def apply_wsearch_off() -> tuple[bool, str]:
    """Отключить индексацию Windows Search — меньше фоновой нагрузки на диск."""
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WSearch", "Start", 4)
    _ps("Stop-Service WSearch -Force -ErrorAction SilentlyContinue")
    return True, "Windows Search indexing disabled (Start menu search will be slower)"


def revert_wsearch_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WSearch", "Start", 2)
    _ps("Start-Service WSearch -ErrorAction SilentlyContinue")
    return True, "Windows Search restored"


def apply_superfetch_off() -> tuple[bool, str]:
    pref = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    set_dword(HKLM, pref, "EnableSuperfetch", 0)
    set_dword(HKLM, pref, "EnablePrefetcher", 0)
    return True, "Superfetch/Prefetch disabled"


def revert_superfetch_on() -> tuple[bool, str]:
    pref = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    set_dword(HKLM, pref, "EnableSuperfetch", 3)
    set_dword(HKLM, pref, "EnablePrefetcher", 3)
    return True, "Superfetch/Prefetch restored"


def apply_welcome_experience_off() -> tuple[bool, str]:
    cdm = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
    set_dword(HKCU, cdm, "SubscribedContent-310093Enabled", 0)
    set_dword(HKCU, cdm, "SubscribedContent-338388Enabled", 0)
    set_dword(HKCU, cdm, "SubscribedContent-353694Enabled", 0)
    set_dword(HKCU, cdm, "SubscribedContent-353696Enabled", 0)
    set_dword(HKCU, cdm, "SoftLandingEnabled", 0)
    return True, "Welcome experience / tips disabled"


def revert_welcome_experience_on() -> tuple[bool, str]:
    cdm = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
    for name in (
        "SubscribedContent-310093Enabled",
        "SubscribedContent-338388Enabled",
        "SubscribedContent-353694Enabled",
        "SubscribedContent-353696Enabled",
        "SoftLandingEnabled",
    ):
        delete_value(HKCU, cdm, name)
    return True, "Welcome experience restored"


def apply_search_highlights_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "EnableDynamicContentInWSB", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\SearchSettings", "IsDynamicSearchBoxEnabled", 0)
    return True, "Search highlights disabled"


def revert_search_highlights_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "EnableDynamicContentInWSB")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\SearchSettings", "IsDynamicSearchBoxEnabled")
    return True, "Search highlights restored"


def apply_tips_suggestions_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableSoftLanding", 1)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures", 1)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338389Enabled", 0)
    return True, "Tips and suggestions disabled"


def revert_tips_suggestions_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableSoftLanding")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338389Enabled")
    return True, "Tips restored"


def apply_shared_experiences_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Start_TrackProgs", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Start_TrackDocs", 0)
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableCdp", 0)
    return True, "Shared experiences / activity feed off"


def revert_shared_experiences_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Start_TrackProgs")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Start_TrackDocs")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableCdp")
    return True, "Shared experiences restored"


def apply_tailored_experiences_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableTailoredExperiencesWithDiagnosticData", 1)
    return True, "Tailored experiences disabled"


def revert_tailored_experiences_on() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Policies\Microsoft\Windows\CloudContent",
        "DisableTailoredExperiencesWithDiagnosticData",
    )
    return True, "Tailored experiences restored"


def apply_news_interests_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Feeds")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Feeds", "EnableFeeds", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 2)
    return True, "News and interests disabled"


def revert_news_interests_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Feeds", "EnableFeeds")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode")
    return True, "News restored"


def apply_store_auto_update_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\WindowsStore")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\WindowsStore", "AutoDownload", 2)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\WindowsStore", "DisableStoreApps", 0)
    return True, "Microsoft Store auto-update disabled"


def revert_store_auto_update_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\WindowsStore", "AutoDownload")
    return True, "Store auto-update restored"


def apply_ntfs_8dot3_off() -> tuple[bool, str]:
    ok, out = _run(["fsutil", "behavior", "set", "disable8dot3", "1"])
    return ok, out or "8.3 names disabled on NTFS volumes"


def revert_ntfs_8dot3_on() -> tuple[bool, str]:
    ok, out = _run(["fsutil", "behavior", "set", "disable8dot3", "0"])
    return ok, out or "8.3 names default"


def apply_hpet_service_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\hpet", "Start", 4)
    _ps("Stop-Service hpet -Force -ErrorAction SilentlyContinue")
    return True, "HPET service disabled — перезагрузка"


def revert_hpet_service_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\hpet", "Start", 3)
    return True, "HPET service restored"


def apply_feedback_ceip_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\SQMClient\Windows")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\SQMClient\Windows", "CEIPEnable", 0)
    set_dword(HKCU, r"Software\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications", 1)
    return True, "Feedback / CEIP disabled"


def revert_feedback_ceip_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\SQMClient\Windows", "CEIPEnable")
    delete_value(HKCU, r"Software\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications")
    return True, "Feedback restored"


def apply_explorer_animations_off() -> tuple[bool, str]:
    adv = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    set_dword(HKCU, adv, "TaskbarAnimations", 0)
    set_dword(HKCU, adv, "ListviewAlphaSelect", 0)
    set_dword(HKCU, adv, "ListviewShadow", 0)
    set_dword(HKCU, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2)
    return True, "Explorer animations disabled"


def revert_explorer_animations_on() -> tuple[bool, str]:
    adv = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    delete_value(HKCU, adv, "TaskbarAnimations")
    delete_value(HKCU, adv, "ListviewAlphaSelect")
    delete_value(HKCU, adv, "ListviewShadow")
    delete_value(HKCU, r"Control Panel\Desktop\WindowMetrics", "MinAnimate")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting")
    return True, "Explorer animations restored"


def apply_background_transfer_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\BITS", "Start", 4)
    return True, "Background Intelligent Transfer disabled"


def revert_background_transfer_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\BITS", "Start", 3)
    return True, "BITS restored"


def apply_sysmain_service_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\SysMain", "Start", 4)
    _ps("Stop-Service SysMain -Force -ErrorAction SilentlyContinue")
    return True, "SysMain (Superfetch service) disabled"


def revert_sysmain_service_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\SysMain", "Start", 2)
    _ps("Start-Service SysMain -ErrorAction SilentlyContinue")
    return True, "SysMain restored"


def apply_mmcss_games_priority() -> tuple[bool, str]:
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    ensure_key(HKLM, path)
    set_dword(HKLM, path, "GPU Priority", 8)
    set_dword(HKLM, path, "Priority", 6)
    set_dword(HKLM, path, "Scheduling Category", 2)
    set_dword(HKLM, path, "SFIO Priority", 2)
    return True, "MMCSS Games profile boosted"


def revert_mmcss_games_priority() -> tuple[bool, str]:
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    for name in ("GPU Priority", "Priority", "Scheduling Category", "SFIO Priority"):
        delete_value(HKLM, path, name)
    return True, "MMCSS Games default"


def apply_disable_usb_hub_suspend() -> tuple[bool, str]:
    script = r"""
Get-PnpDevice -Class USB -ErrorAction SilentlyContinue | ForEach-Object {
    $id = $_.InstanceId
    if ($id) {
        $p = "HKLM:\SYSTEM\CurrentControlSet\Enum\$id\Device Parameters"
        if (Test-Path $p) {
            Set-ItemProperty -Path $p -Name SelectiveSuspendEnabled -Value 0 -Type DWord -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $p -Name EnhancedPowerManagementEnabled -Value 0 -Type DWord -ErrorAction SilentlyContinue
        }
    }
}
'USB hub selective suspend disabled on devices'
"""
    return _ps(script)


def revert_disable_usb_hub_suspend() -> tuple[bool, str]:
    return True, "USB hub power — переподключите USB или перезагрузите ПК для полного отката"
