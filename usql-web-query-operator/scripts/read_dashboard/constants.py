"""Constants shared by dashboard discovery and profiling commands."""

from __future__ import annotations

from pathlib import Path


DASHBOARD_MARKET_URL = "https://uanalysis.baijia.com/dashboard-market"
DASHBOARD_MENU_API = "https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage"
DASHBOARD_CONFIG_API = "https://uanalysis.baijia.com/uanalysis-intelligence/config/dashBoard"
UNIT_DETAIL_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/unit/consumer/detail"
PUBLIC_FILTER_DETAIL_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail"
UNIT_VALUE_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/unit"

DEFAULT_PROFILE_ALL_FOLDERS = ("市场顾问数据", "青橙项目部")

SKILLS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WEB_PROFILE_DIR = SKILLS_ROOT / "sql-query-writer-for-dashboard" / "knowledge" / "dashboard_web_profiles"
DEFAULT_WEB_PROFILE_README = DEFAULT_WEB_PROFILE_DIR / "README.md"
DEFAULT_DASHBOARDS_README = SKILLS_ROOT / "sql-query-writer-for-dashboard" / "knowledge" / "dashboards" / "README.md"
DEFAULT_CHANGELOG = SKILLS_ROOT / "sql-query-writer-for-dashboard" / "knowledge" / "update_log" / "changelog.md"

DASHBOARD_FILENAME_OVERRIDES = {
    "dashboard_3699054046816116737": "consultant_process_data_dimension_web_profile.md",
    "dashboard_3706108893345009664": "consultant_attendance_data_dimension_web_profile.md",
    "dashboard_3730722176629411841": "outbound_call_process_dashboard_web_profile.md",
    "dashboard_3733927793301065728": "qingcheng_process_data_report_web_profile.md",
    "dashboard_3748410696516800512": "market_consultant_attendance_report_web_profile.md",
    "dashboard_3759973841100165121": "operation_side_dashboard_web_profile.md",
    "dashboard_3765824192103694336": "qingcheng_attendance_report_web_profile.md",
    "dashboard_3767151344579387392": "market_consultant_conversion_web_profile.md",
    "dashboard_3791961955008733184": "market_consultant_volume_pace_web_profile.md",
    "dashboard_3804681042591760385": "market_consultant_user_profile_analysis_web_profile.md",
    "dashboard_3822396843512627200": "market_consultant_evaluation_web_profile.md",
    "dashboard_3833805337379700736": "boss11_operation_side_dashboard_web_profile.md",
    "dashboard_3839499028752805888": "evaluation_broadcast_text_web_profile.md",
    "dashboard_3845252580183867393": "process_broadcast_text_web_profile.md",
    "dashboard_3852445620602875904": "qingcheng_all_product_dashboard_web_profile.md",
    "dashboard_3861041931986931712": "multi_dimensional_timeliness_analysis_douzi_web_profile.md",
    "dashboard_3865509979877412864": "qingcheng_full_grade_revenue_dashboard_web_profile.md",
    "dashboard_3872626876332130305": "qingcheng_team_conversion_completion_web_profile.md",
    "dashboard_3873038327756636161": "qingcheng_personal_conversion_web_profile.md",
    "dashboard_3874439982521286657": "newcomer_early_stage_process_conversion_web_profile.md",
    "dashboard_3881610656431284224": "kunlun_summer_incentive_web_profile.md",
    "dashboard_3884629814875697153": "qingcheng_dousi_conversion_web_profile.md",
    "dashboard_3885764906392891392": "qingcheng_conversion_dashboard_web_profile.md",
    "dashboard_3893277592797257728": "qingcheng_completion_broadcast_text_web_profile.md",
    "dashboard_3910621974690701312": "qingcheng_channel_process_daily_web_profile.md",
}
