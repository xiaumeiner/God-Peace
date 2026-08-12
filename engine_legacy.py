"""Adapter that exposes bundled calamity engine functions under engine: prefix.

This lets the new tweaks.catalog_loader resolve apply/revert functions as
'engine:apply_game_dvr_off' while reusing the existing bundled engine code.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CALAMITY_DIR = Path(__file__).resolve().parent / "bundled" / "calamity"
if str(_CALAMITY_DIR) not in sys.path:
    sys.path.insert(0, str(_CALAMITY_DIR))

# Import all apply/revert functions so catalog.json can reference them.
from engine import (  # noqa: F401
    apply_audio_mmcss_pro,
    apply_auto_end_tasks,
    apply_background_apps_off,
    apply_bcd_timer_tweaks,
    apply_content_delivery_off,
    apply_core_parking_off,
    apply_cortana_off,
    apply_cpu_priority,
    apply_csrss_priority,
    apply_cs2_priority,
    apply_defender_off,
    apply_delivery_optimization_off,
    apply_desktop_responsiveness,
    apply_disable_cstates,
    apply_disable_dynamic_pstate,
    apply_disable_fso_global,
    apply_disable_mpo,
    apply_disable_page_combining,
    apply_disable_pointer_shadow,
    apply_disable_prefetch_gaming,
    apply_disable_print_spooler,
    apply_disable_vbs,
    apply_distribute_timers,
    apply_dwm_animations_off,
    apply_energy_logging_off,
    apply_fth_off,
    apply_game_dvr_off,
    apply_game_mode_on,
    apply_game_profile,
    apply_gpu_energy_drv_off,
    apply_gpu_preemption,
    apply_gpu_power_latency_pack,
    apply_gpu_thread_priority,
    apply_graphics_latency,
    apply_gta5_priority,
    apply_hags,
    apply_hibernate_off,
    apply_hidusb_low_latency,
    apply_input_layered_latency,
    apply_io_page_lock_limit,
    apply_keyboard_fast_delays,
    apply_keyboard_queue_size,
    apply_latency_sensitive_games,
    apply_location_off,
    apply_maintenance_off,
    apply_memory_compression_off,
    apply_memory_gaming,
    apply_mmcss_aggressive,
    apply_monitor_latency,
    apply_mouse_1to1,
    apply_mouse_queue_size,
    apply_msi_gpu,
    apply_msi_network,
    apply_msi_usb,
    apply_ndu_off,
    apply_nic_power_off,
    apply_nvidia_driver_tweaks,
    apply_nvidia_telemetry_off,
    apply_nvidia_write_combining_off,
    apply_power_latency_pack,
    apply_power_throttling_off,
    apply_raw_input_priority,
    apply_ssd_trim,
    apply_sysmain_off,
    apply_tcp_low_latency,
    apply_telemetry_policies_off,
    apply_timer_resolution,
    apply_transparency_off,
    apply_ultimate_power_plan,
    apply_usb_selective_suspend_off,
    apply_valorant_priority,
    apply_widgets_off,
    apply_windowed_games_opt,
    apply_xbox_services_off,
    revert_audio_mmcss_pro,
    revert_auto_end_tasks,
    revert_background_apps_on,
    revert_bcd_timer_tweaks,
    revert_content_delivery_on,
    revert_core_parking_on,
    revert_cortana_on,
    revert_cpu_priority,
    revert_csrss_priority,
    revert_cs2_priority,
    revert_defender_on,
    revert_delivery_optimization_on,
    revert_desktop_responsiveness,
    revert_disable_cstates,
    revert_disable_dynamic_pstate,
    revert_disable_fso_global,
    revert_disable_mpo,
    revert_disable_page_combining,
    revert_disable_pointer_shadow,
    revert_disable_prefetch_gaming,
    revert_disable_print_spooler,
    revert_disable_vbs,
    revert_distribute_timers,
    revert_dwm_animations_on,
    revert_energy_logging_on,
    revert_fth_on,
    revert_game_dvr_on,
    revert_game_mode_off,
    revert_game_profile,
    revert_gpu_energy_drv_on,
    revert_gpu_preemption,
    revert_gpu_power_latency_pack,
    revert_gpu_thread_priority,
    revert_graphics_latency,
    revert_gta5_priority,
    revert_hags,
    revert_hidusb_low_latency,
    revert_high_performance_plan,
    revert_hibernate_on,
    revert_input_layered_latency,
    revert_io_page_lock_limit,
    revert_keyboard_fast_delays,
    revert_keyboard_queue_size,
    revert_latency_sensitive_games,
    revert_location_on,
    revert_maintenance_on,
    revert_memory_compression_on,
    revert_memory_gaming,
    revert_mmcss_aggressive,
    revert_monitor_latency,
    revert_mouse_default,
    revert_mouse_queue_size,
    revert_msi_gpu,
    revert_msi_network,
    revert_msi_usb,
    revert_ndu_on,
    revert_nic_power_on,
    revert_nvidia_driver_tweaks,
    revert_nvidia_telemetry_on,
    revert_nvidia_write_combining_on,
    revert_power_latency_pack,
    revert_power_throttling_on,
    revert_raw_input_priority,
    revert_ssd_trim_info,
    revert_sysmain_on,
    revert_tcp_default,
    revert_telemetry_policies_on,
    revert_transparency_on,
    revert_usb_selective_suspend_on,
    revert_valorant_priority,
    revert_widgets_on,
    revert_windowed_games_opt,
    revert_xbox_services_on,
)
import engine_extra as _engine_extra  # noqa: E402
import nvidia as _nvidia  # noqa: E402

# Expose nvidia profile inspector functions used by catalog.json
apply_nvidia_profile_inspector = _nvidia.apply_nvidia_profile_inspector
revert_nvidia_profile_info = _nvidia.revert_nvidia_profile_info

# Expose engine_extra functions used by catalog.json
apply_fast_startup_off = _engine_extra.apply_fast_startup_off
revert_fast_startup_on = _engine_extra.revert_fast_startup_on
apply_large_system_cache_on = _engine_extra.apply_large_system_cache_on
revert_large_system_cache_off = _engine_extra.revert_large_system_cache_off
apply_superfetch_off = _engine_extra.apply_superfetch_off
revert_superfetch_on = _engine_extra.revert_superfetch_on
apply_llmnr_off = _engine_extra.apply_llmnr_off
revert_llmnr_on = _engine_extra.revert_llmnr_on
apply_netbios_off = _engine_extra.apply_netbios_off
revert_netbios_on = _engine_extra.revert_netbios_on
apply_sticky_keys_off = _engine_extra.apply_sticky_keys_off
revert_sticky_keys_on = _engine_extra.revert_sticky_keys_on
apply_lock_screen_blur_off = _engine_extra.apply_lock_screen_blur_off
revert_lock_screen_blur_on = _engine_extra.revert_lock_screen_blur_on
apply_activity_history_off = _engine_extra.apply_activity_history_off
revert_activity_history_on = _engine_extra.revert_activity_history_on
apply_storage_sense_off = _engine_extra.apply_storage_sense_off
revert_storage_sense_on = _engine_extra.revert_storage_sense_on
apply_remote_assistance_off = _engine_extra.apply_remote_assistance_off
revert_remote_assistance_on = _engine_extra.revert_remote_assistance_on
apply_pca_off = _engine_extra.apply_pca_off
revert_pca_on = _engine_extra.revert_pca_on
apply_onedrive_policy_off = _engine_extra.apply_onedrive_policy_off
revert_onedrive_policy_on = _engine_extra.revert_onedrive_policy_on
apply_bluetooth_off = _engine_extra.apply_bluetooth_off
revert_bluetooth_on = _engine_extra.revert_bluetooth_on
apply_wlan_off = _engine_extra.apply_wlan_off
revert_wlan_on = _engine_extra.revert_wlan_on
apply_ntfs_last_access_off = _engine_extra.apply_ntfs_last_access_off
revert_ntfs_last_access_on = _engine_extra.revert_ntfs_last_access_on
apply_web_search_off = _engine_extra.apply_web_search_off
revert_web_search_on = _engine_extra.revert_web_search_on
apply_smartscreen_off = _engine_extra.apply_smartscreen_off
revert_smartscreen_on = _engine_extra.revert_smartscreen_on
apply_maps_broker_off = _engine_extra.apply_maps_broker_off
revert_maps_broker_on = _engine_extra.revert_maps_broker_on
apply_fax_off = _engine_extra.apply_fax_off
revert_fax_on = _engine_extra.revert_fax_on
apply_remote_registry_off = _engine_extra.apply_remote_registry_off
revert_remote_registry_on = _engine_extra.revert_remote_registry_on
apply_consumer_features_off = _engine_extra.apply_consumer_features_off
revert_consumer_features_on = _engine_extra.revert_consumer_features_on
apply_chat_taskbar_off = _engine_extra.apply_chat_taskbar_off
revert_chat_taskbar_on = _engine_extra.revert_chat_taskbar_on
apply_snap_assist_off = _engine_extra.apply_snap_assist_off
revert_snap_assist_on = _engine_extra.revert_snap_assist_on
apply_transparency_blur_off = _engine_extra.apply_transparency_blur_off
revert_transparency_blur_on = _engine_extra.revert_transparency_blur_on
apply_tcp_interface_nodelay = _engine_extra.apply_tcp_interface_nodelay
revert_tcp_interface_nodelay = _engine_extra.revert_tcp_interface_nodelay
apply_spectre_meltdown_off = _engine_extra.apply_spectre_meltdown_off
revert_spectre_meltdown_on = _engine_extra.revert_spectre_meltdown_on
apply_tsx_off = _engine_extra.apply_tsx_off
revert_tsx_on = _engine_extra.revert_tsx_on
apply_svchost_ungroup = _engine_extra.apply_svchost_ungroup
revert_svchost_ungroup = _engine_extra.revert_svchost_ungroup
apply_edge_startup_off = _engine_extra.apply_edge_startup_off
revert_edge_startup_on = _engine_extra.revert_edge_startup_on
apply_insider_service_off = _engine_extra.apply_insider_service_off
revert_insider_service_on = _engine_extra.revert_insider_service_on
apply_mouse_trails_off = _engine_extra.apply_mouse_trails_off
revert_mouse_trails_on = _engine_extra.revert_mouse_trails_on
apply_gamebar_presence_off = _engine_extra.apply_gamebar_presence_off
revert_gamebar_presence_on = _engine_extra.revert_gamebar_presence_on
apply_gamebar_policy_off = _engine_extra.apply_gamebar_policy_off
revert_gamebar_policy_on = _engine_extra.revert_gamebar_policy_on
apply_visual_performance_max = _engine_extra.apply_visual_performance_max
revert_visual_performance_max = _engine_extra.revert_visual_performance_max
apply_wsearch_off = _engine_extra.apply_wsearch_off
revert_wsearch_on = _engine_extra.revert_wsearch_on
apply_explorer_animations_off = _engine_extra.apply_explorer_animations_off
revert_explorer_animations_on = _engine_extra.revert_explorer_animations_on
apply_background_transfer_off = _engine_extra.apply_background_transfer_off
revert_background_transfer_on = _engine_extra.revert_background_transfer_on
apply_sysmain_service_off = _engine_extra.apply_sysmain_service_off
revert_sysmain_service_on = _engine_extra.revert_sysmain_service_on
apply_mmcss_games_priority = _engine_extra.apply_mmcss_games_priority
revert_mmcss_games_priority = _engine_extra.revert_mmcss_games_priority
apply_disable_usb_hub_suspend = _engine_extra.apply_disable_usb_hub_suspend
revert_disable_usb_hub_suspend = _engine_extra.revert_disable_usb_hub_suspend
apply_welcome_experience_off = _engine_extra.apply_welcome_experience_off
revert_welcome_experience_on = _engine_extra.revert_welcome_experience_on
apply_search_highlights_off = _engine_extra.apply_search_highlights_off
revert_search_highlights_on = _engine_extra.revert_search_highlights_on
apply_tips_suggestions_off = _engine_extra.apply_tips_suggestions_off
revert_tips_suggestions_on = _engine_extra.revert_tips_suggestions_on
apply_shared_experiences_off = _engine_extra.apply_shared_experiences_off
revert_shared_experiences_on = _engine_extra.revert_shared_experiences_on
apply_tailored_experiences_off = _engine_extra.apply_tailored_experiences_off
revert_tailored_experiences_on = _engine_extra.revert_tailored_experiences_on
apply_news_interests_off = _engine_extra.apply_news_interests_off
revert_news_interests_on = _engine_extra.revert_news_interests_on
apply_store_auto_update_off = _engine_extra.apply_store_auto_update_off
revert_store_auto_update_on = _engine_extra.revert_store_auto_update_on
apply_ntfs_8dot3_off = _engine_extra.apply_ntfs_8dot3_off
revert_ntfs_8dot3_on = _engine_extra.revert_ntfs_8dot3_on
apply_feedback_ceip_off = _engine_extra.apply_feedback_ceip_off
revert_feedback_ceip_on = _engine_extra.revert_feedback_ceip_on
apply_hpet_platform_tick = _engine_extra.apply_hpet_platform_tick
revert_hpet_platform_tick = _engine_extra.revert_hpet_platform_tick
apply_hpet_service_off = _engine_extra.apply_hpet_service_off
revert_hpet_service_on = _engine_extra.revert_hpet_service_on

# Expose engine functions referenced by catalog.json but not in main import block
import engine as _engine  # noqa: E402

apply_usb_power_saving_off = _engine.apply_usb_power_saving_off
revert_usb_power_saving_on = lambda: (True, "Ручной сброс в диспетчере устройств")
apply_notifications_off = _engine.apply_notifications_off
revert_notifications_on = _engine.revert_notifications_on
apply_network_throttle_off = _engine.apply_network_throttle_off
revert_network_throttle_on = _engine.revert_network_throttle_on
apply_dns_cloudflare = _engine.apply_dns_cloudflare
revert_dns_dhcp = _engine.revert_dns_dhcp
