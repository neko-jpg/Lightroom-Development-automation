"""
Main Window for Junmai AutoDev GUI (PyQt6)
Desktop dashboard + guided flow experience.
"""

from __future__ import annotations

from typing import List

import os
import subprocess
import sys
from pathlib import Path

import requests
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QRunnable, QThreadPool
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_VERSION = "2.0.0"


# ---------------------------------------------------------------------------
# Guided workflow helpers
# ---------------------------------------------------------------------------


class WorkerSignals(QObject):
    """Signals shared by worker runnables."""

    success = pyqtSignal(object)
    error = pyqtSignal(str)


class JobSubmissionWorker(QRunnable):
    """POSTs prompts to the local_bridge API without blocking the UI thread."""

    def __init__(self, prompt: str, api_url: str):
        super().__init__()
        self.prompt = prompt
        self.api_url = api_url
        self.signals = WorkerSignals()

    def run(self) -> None:  # pragma: no cover - executed in worker thread
        try:
            response = requests.post(
                self.api_url,
                json={"prompt": self.prompt},
                timeout=30,
            )
            response.raise_for_status()
            self.signals.success.emit(response.json())
        except Exception as exc:  # noqa: BLE001 - propagate message to UI
            self.signals.error.emit(str(exc))


class QueueStatusWorker(QRunnable):
    """Queries queue and config endpoints to derive a friendly status message."""

    def __init__(self, queue_url: str, config_url: str):
        super().__init__()
        self.queue_url = queue_url
        self.config_url = config_url
        self.signals = WorkerSignals()

    def run(self) -> None:  # pragma: no cover - executed in worker thread
        try:
            response = requests.get(self.queue_url, timeout=4)
            response.raise_for_status()
            payload = {"mode": "stats", "data": response.json()}
        except Exception:
            try:
                response = requests.get(self.config_url, timeout=3)
                response.raise_for_status()
                payload = {"mode": "config", "data": response.json()}
            except Exception as exc:  # noqa: BLE001 - propagate message to UI
                self.signals.error.emit(str(exc))
                return

        self.signals.success.emit(payload)


class GuidedFlowWidget(QWidget):
    """Beginner-friendly storyboard that walks users through the workflow."""

    PROMPT_TEMPLATES = [
        {
            "title": "やわらかい人物写真",
            "subtitle": "自然光 × 透明感",
            "prompt": "逆光のポートレートを透け感のある柔らかな肌質で、"
            "ハイライトは抑え、スキントーンをなめらかに整える",
        },
        {
            "title": "都会の夜景",
            "subtitle": "ネオン × コントラスト",
            "prompt": "夜の街スナップ。黒を締めつつネオンの色を保ち、"
            "微かな霧を足して映画的な雰囲気に",
        },
        {
            "title": "旅行の空と海",
            "subtitle": "鮮やか × 立体感",
            "prompt": "日中の海辺。青空は濃くしすぎず、海の透明感を残したまま"
            "砂浜を明るく起こすフィルム調",
        },
        {
            "title": "ドラマチックなモノクロ",
            "subtitle": "粒状感 × 深み",
            "prompt": "陰影が強いモノクロポートレート。コントラストを高め、"
            "微粒子をのせてクラシックフィルムの質感に仕上げる",
        },
    ]

    API_URL = "http://127.0.0.1:5100/job"
    QUEUE_URL = "http://127.0.0.1:5100/queue/stats"
    CONFIG_URL = "http://127.0.0.1:5100/config"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.template_buttons: List[QPushButton] = []

        self._build_ui()
        self._connect_signals()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_queue_status)
        self.status_timer.start(7000)
        self.refresh_queue_status()

    # UI construction -----------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        hero = QLabel("3つのステップで \"簡単にできる\" を実現")
        hero.setWordWrap(True)
        hero_font = QFont()
        hero_font.setPointSize(18)
        hero_font.setBold(True)
        hero.setFont(hero_font)
        layout.addWidget(hero)

        sub = QLabel("① 雰囲気を選ぶ → ② 仕上がりを確認 → ③ Lightroomへ送信。"
                     "あとはJunmai AutoDevにおまかせです。")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        layout.addWidget(self._build_step_one())
        layout.addWidget(self._build_step_two())
        layout.addWidget(self._build_step_three())
        layout.addStretch()

    def _build_step_one(self) -> QWidget:
        container = QGroupBox("Step 1 · 雰囲気を選ぶ")
        inner_layout = QVBoxLayout(container)
        inner_layout.addWidget(QLabel("テンプレートを選ぶか、直接あなたの言葉で入力できます。"))

        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, template in enumerate(self.PROMPT_TEMPLATES):
            button = QPushButton(f"{template['title']}\n{template['subtitle']}")
            button.setCheckable(True)
            button.setMinimumHeight(64)
            button.clicked.connect(lambda _, t=template, b=button: self.apply_template(t, b))
            self.template_buttons.append(button)
            grid.addWidget(button, idx // 2, idx % 2)
        inner_layout.addLayout(grid)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("仕上げたい雰囲気を入力してください...")
        self.prompt_input.textChanged.connect(self.update_preview_notes)
        inner_layout.addWidget(self.prompt_input)

        return container

    def _build_step_two(self) -> QWidget:
        container = QGroupBox("Step 2 · 仕上がりのプレビュー")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("プロンプトから自動で読み取った調整方針です。"))

        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        self.update_preview_notes()

        return container

    def _build_step_three(self) -> QWidget:
        container = QGroupBox("Step 3 · Lightroomへ送信")
        layout = QVBoxLayout(container)

        self.queue_status_label = QLabel("Bridge: 状態を取得中...")
        self.queue_status_label.setWordWrap(True)
        layout.addWidget(self.queue_status_label)

        self.auto_hint_label = QLabel("ボタンを押すだけで、仮想コピーと安全な適用を自動で行います。")
        self.auto_hint_label.setWordWrap(True)
        layout.addWidget(self.auto_hint_label)

        self.submit_button = QPushButton("Lightroom に送信する")
        self.submit_button.setMinimumHeight(46)
        self.submit_button.clicked.connect(self.submit_prompt)
        layout.addWidget(self.submit_button)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        return container

    def _connect_signals(self) -> None:
        pass  # Placeholder for future expansions (e.g., local events)

    # Preview + template handling ----------------------------------------

    def apply_template(self, template: dict, button: QPushButton) -> None:
        for btn in self.template_buttons:
            if btn is not button:
                btn.setChecked(False)
        button.setChecked(True)
        self.prompt_input.setPlainText(template["prompt"])
        self.update_preview_notes()

    def update_preview_notes(self) -> None:
        notes = self._generate_preview_notes(self.prompt_input.toPlainText())
        self.preview_list.clear()
        for note in notes:
            item = QListWidgetItem(f"• {note}")
            self.preview_list.addItem(item)

    def _generate_preview_notes(self, prompt: str) -> List[str]:
        prompt_lower = prompt.lower()
        notes: List[str] = []

        if any(word in prompt_lower for word in ["portrait", "ポートレート", "肌", "skin"]):
            notes.append("肌の質感を守りつつハイライトを抑えて透け感をキープします。")
        if any(word in prompt_lower for word in ["night", "夜", "ネオン"]):
            notes.append("夜景のネオンを保ったまま、黒レベルと霧を微調整します。")
        if any(word in prompt_lower for word in ["film", "フィルム", "grain"]):
            notes.append("粒状感を軽くのせ、落ち着いたコントラストでフィルム調に。")
        if any(word in prompt_lower for word in ["sea", "ocean", "海", "空"]):
            notes.append("青系は彩度を暴発させず、砂浜と肌を柔らかく明るくします。")
        if not notes:
            notes.append("露出と彩度を安全域で調整し、スキントーンに優しい設定で適用します。")

        return notes

    # Queue + submission handling ----------------------------------------

    def refresh_queue_status(self) -> None:
        worker = QueueStatusWorker(self.QUEUE_URL, self.CONFIG_URL)
        worker.signals.success.connect(self._on_queue_status)
        worker.signals.error.connect(self._on_queue_error)
        self.thread_pool.start(worker)

    def _on_queue_status(self, payload: dict) -> None:
        mode = payload.get("mode")
        if mode == "stats":
            data = payload.get("data", {})
            pending = data.get("total_pending", 0)
            active = data.get("active_tasks", 0)
            self.queue_status_label.setText(
                f"Bridge: 稼働中 · {pending}件待機 / {active}件処理中"
            )
        else:
            self.queue_status_label.setText("Bridge: 接続済み · 詳細情報を取得中")

    def _on_queue_error(self, message: str) -> None:
        self.queue_status_label.setText(
            "Bridge: 未接続。アプリが自動で再接続を試みています。"
        )
        self.result_label.setText(f"ステータス取得に失敗しました: {message}")

    def submit_prompt(self) -> None:
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.result_label.setText("プロンプトを入力してください。")
            return

        self.submit_button.setEnabled(False)
        self.submit_button.setText("送信中...")
        self.result_label.setText("Lightroomへジョブを登録しています。")

        worker = JobSubmissionWorker(prompt, self.API_URL)
        worker.signals.success.connect(self._on_submit_success)
        worker.signals.error.connect(self._on_submit_error)
        self.thread_pool.start(worker)

    def _on_submit_success(self, data: dict) -> None:
        job_id = data.get("jobId", "unknown")
        self.result_label.setText(
            f"✔ Lightroomへの送信が完了しました (Job ID: {job_id})。"
            " 処理が終わると自動で仮想コピーが作成されます。"
        )
        self.submit_button.setEnabled(True)
        self.submit_button.setText("Lightroom に送信する")

    def _on_submit_error(self, message: str) -> None:
        self.result_label.setText(f"送信に失敗しました: {message}")
        self.submit_button.setEnabled(True)
        self.submit_button.setText("Lightroom に送信する")

    def shutdown(self) -> None:
        if hasattr(self, "status_timer") and self.status_timer.isActive():
            self.status_timer.stop()


# ---------------------------------------------------------------------------
# Legacy/advanced tabs
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """
    Junmai AutoDev main window with both guided and advanced experiences.

    guided_mode:
        When True, show the beginner-friendly guided tab as the first tab.
    """

    def __init__(self, guided_mode: bool = True):
        super().__init__()
        self.guided_mode = guided_mode
        self.init_ui()
        self.setup_status_bar()
        self.setup_timers()

    def init_ui(self) -> None:
        """Initializes the main UI layout."""
        self.setWindowTitle("Junmai AutoDev")
        self.setGeometry(100, 100, 1280, 820)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        if self.guided_mode:
            self.add_guided_tab()
        self.add_dashboard_tab()
        self.add_sessions_tab()
        self.add_approval_tab()
        self.add_presets_tab()
        self.add_settings_tab()
        self.add_logs_tab()

    def add_guided_tab(self) -> None:
        """Adds the simplified Guided Flow tab."""
        self.guided_flow_widget = GuidedFlowWidget()
        self.tab_widget.addTab(self.guided_flow_widget, "✨ Guided Flow")

    def add_dashboard_tab(self) -> None:
        """Dashboard tab with status and quick actions."""
        from widgets.dashboard_widgets import (
            SystemStatusWidget,
            ActiveSessionsWidget,
            RecentActivityWidget,
            QuickActionsWidget,
        )

        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.system_status_widget = SystemStatusWidget()
        layout.addWidget(self.system_status_widget)

        self.active_sessions_widget = ActiveSessionsWidget()
        self.active_sessions_widget.session_clicked.connect(self.on_session_clicked)
        layout.addWidget(self.active_sessions_widget, 1)

        self.quick_actions_widget = QuickActionsWidget()
        self.quick_actions_widget.add_hotfolder_clicked.connect(self.on_add_hotfolder)
        self.quick_actions_widget.settings_clicked.connect(self.on_settings_clicked)
        self.quick_actions_widget.statistics_clicked.connect(self.on_statistics_clicked)
        self.quick_actions_widget.approval_queue_clicked.connect(
            self.on_approval_queue_clicked
        )
        self.quick_actions_widget.export_now_clicked.connect(self.on_export_now_clicked)
        layout.addWidget(self.quick_actions_widget)

        self.recent_activity_widget = RecentActivityWidget()
        layout.addWidget(self.recent_activity_widget, 1)

        self.tab_widget.addTab(dashboard, "📊 Dashboard")

    def add_sessions_tab(self) -> None:
        """Session management tab."""
        from widgets.session_widgets import SessionManagementWidget

        self.session_management_widget = SessionManagementWidget()
        self.tab_widget.addTab(self.session_management_widget, "📁 Sessions")

    def add_approval_tab(self) -> None:
        """Approval queue tab."""
        from widgets.approval_widgets import ApprovalQueueWidget

        self.approval_queue_widget = ApprovalQueueWidget()
        self.tab_widget.addTab(self.approval_queue_widget, "✅ Approval")

    def add_presets_tab(self) -> None:
        """Preset management placeholder tab."""
        presets = QWidget()
        layout = QVBoxLayout(presets)
        label = QLabel("Preset manager coming soon. Guided Flowプリセットで操作できます。")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.tab_widget.addTab(presets, "🎛 Presets")

    def add_settings_tab(self) -> None:
        """Settings tab."""
        from widgets.settings_widgets import SettingsWidget

        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_saved.connect(self.on_settings_saved)
        self.tab_widget.addTab(self.settings_widget, "🛠 Settings")

    def add_logs_tab(self) -> None:
        """Logs tab placeholder."""
        logs = QWidget()
        layout = QVBoxLayout(logs)
        label = QLabel("Logs - backend server output and activity summaries.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.tab_widget.addTab(logs, "🗒 Logs")

    def setup_status_bar(self) -> None:
        """Creates persistent status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("System: Ready")
        self.status_bar.addWidget(self.status_label)
        self.lightroom_label = QLabel("Lightroom: Disconnected")
        self.status_bar.addPermanentWidget(self.lightroom_label)

        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setObjectName("versionLabel")
        self.status_bar.addPermanentWidget(self.version_label)

        self.open_logs_button = QPushButton("ログフォルダを開く")
        self.open_logs_button.setObjectName("openLogsButton")
        self.open_logs_button.clicked.connect(self.on_open_logs_clicked)
        self.status_bar.addPermanentWidget(self.open_logs_button)

    def setup_timers(self) -> None:
        """Starts global timers."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)

    def update_status(self) -> None:
        """Refreshes status bar messaging."""
        # Placeholder: integrate real metrics in future tasks.
        pass

    # --- Event handlers -------------------------------------------------

    def on_session_clicked(self, session_id: int) -> None:
        self.tab_widget.setCurrentIndex(2 if self.guided_mode else 1)
        print(f"Session clicked: {session_id}")

    def on_add_hotfolder(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Hot Folder",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            print(f"Add hot folder: {folder}")

    def on_settings_clicked(self) -> None:
        target_index = 5 if self.guided_mode else 4
        self.tab_widget.setCurrentIndex(target_index)

    def on_statistics_clicked(self) -> None:
        target_label = "📊 Statistics"
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == target_label:
                self.tab_widget.setCurrentIndex(i)
                return

        from widgets.statistics_widgets import StatisticsWidget

        statistics_widget = StatisticsWidget()
        self.tab_widget.addTab(statistics_widget, target_label)
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def on_approval_queue_clicked(self) -> None:
        target_index = 3 if self.guided_mode else 2
        self.tab_widget.setCurrentIndex(target_index)

    def on_export_now_clicked(self) -> None:
        print("Export now clicked")

    def on_settings_saved(self) -> None:
        if hasattr(self, "system_status_widget"):
            self.system_status_widget.update_status()
        self.status_bar.showMessage("Settings saved successfully", 3000)

    def on_open_logs_clicked(self) -> None:
        """Opens the logs directory in the OS file explorer."""
        logs_path = self._ensure_logs_directory()
        try:
            if sys.platform == "win32":
                os.startfile(logs_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(logs_path)])
            else:
                subprocess.Popen(["xdg-open", str(logs_path)])
        except Exception as exc:  # noqa: BLE001 - surfaced to user
            self.status_bar.showMessage(f"ログフォルダを開けませんでした: {exc}", 5000)

    def _ensure_logs_directory(self) -> Path:
        """Returns the most likely logs directory, creating it if necessary."""
        candidates = [
            Path.cwd() / "logs",
            Path(__file__).resolve().parent.parent / "logs",
        ]
        for path in candidates:
            if path.exists():
                return path

        default_path = candidates[0]
        default_path.mkdir(parents=True, exist_ok=True)
        return default_path

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        if hasattr(self, "status_timer"):
            self.status_timer.stop()

        if hasattr(self, "system_status_widget"):
            self.system_status_widget.update_timer.stop()
        if hasattr(self, "active_sessions_widget"):
            self.active_sessions_widget.update_timer.stop()
        if hasattr(self, "recent_activity_widget"):
            self.recent_activity_widget.update_timer.stop()
        if hasattr(self, "quick_actions_widget"):
            self.quick_actions_widget.update_timer.stop()
        if hasattr(self, "session_management_widget"):
            self.session_management_widget.session_list.update_timer.stop()
        if hasattr(self, "guided_flow_widget"):
            self.guided_flow_widget.shutdown()

        event.accept()
