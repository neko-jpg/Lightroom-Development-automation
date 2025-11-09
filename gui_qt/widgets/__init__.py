"""
Widgets package for Junmai AutoDev GUI
"""

from .dashboard_widgets import (
    SystemStatusWidget,
    ActiveSessionsWidget,
    RecentActivityWidget,
    QuickActionsWidget
)

from .session_widgets import (
    SessionListWidget,
    SessionDetailWidget,
    SessionManagementWidget
)

from .approval_widgets import (
    PhotoComparisonWidget,
    AIEvaluationWidget,
    ParameterDetailsWidget,
    ApprovalActionsWidget,
    ApprovalQueueWidget
)

from .settings_widgets import (
    SettingsWidget,
    HotFolderSettingsWidget,
    AISettingsWidget,
    ProcessingSettingsWidget,
    NotificationSettingsWidget,
    UISettingsWidget
)

from .statistics_widgets import (
    StatisticsWidget,
    PresetUsageWidget
)

__all__ = [
    'SystemStatusWidget',
    'ActiveSessionsWidget',
    'RecentActivityWidget',
    'QuickActionsWidget',
    'SessionListWidget',
    'SessionDetailWidget',
    'SessionManagementWidget',
    'PhotoComparisonWidget',
    'AIEvaluationWidget',
    'ParameterDetailsWidget',
    'ApprovalActionsWidget',
    'ApprovalQueueWidget',
    'SettingsWidget',
    'HotFolderSettingsWidget',
    'AISettingsWidget',
    'ProcessingSettingsWidget',
    'NotificationSettingsWidget',
    'UISettingsWidget',
    'StatisticsWidget',
    'PresetUsageWidget'
]
