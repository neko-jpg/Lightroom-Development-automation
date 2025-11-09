"""
Statistics and Report Widgets for Junmai AutoDev GUI
統計・レポート画面用ウィジェット群

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import json
import csv
from io import BytesIO


class StatisticsWidget(QWidget):
    """
    統計・レポート画面のメインウィジェット
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    - 日次・週次・月次統計表示
    - グラフ表示（matplotlib統合）
    - プリセット使用頻度の可視化
    - CSV/PDFエクスポート機能
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.current_period = "daily"  # daily, weekly, monthly
        self.init_ui()
        
        # 定期更新タイマー（30秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(30000)
        
        # 初回更新
        self.update_statistics()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title = QLabel("Statistics & Reports")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 期間選択
        period_label = QLabel("Period:")
        header_layout.addWidget(period_label)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        header_layout.addWidget(self.period_combo)
        
        # エクスポートボタン
        self.export_csv_btn = QPushButton("📄 Export CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(self.export_csv_btn)
        
        self.export_pdf_btn = QPushButton("📑 Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        header_layout.addWidget(self.export_pdf_btn)
        
        layout.addLayout(header_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 概要タブ
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 Overview")
        
        # グラフタブ
        self.charts_tab = self.create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "📈 Charts")
        
        # プリセットタブ
        self.presets_tab = self.create_presets_tab()
        self.tab_widget.addTab(self.presets_tab, "🎨 Presets")
        
        layout.addWidget(self.tab_widget)
    
    def create_overview_tab(self) -> QWidget:
        """概要タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        
        # サマリーカード
        self.summary_widget = self.create_summary_widget()
        container_layout.addWidget(self.summary_widget)
        
        # 処理統計
        self.processing_stats_widget = self.create_processing_stats_widget()
        container_layout.addWidget(self.processing_stats_widget)
        
        # 品質統計
        self.quality_stats_widget = self.create_quality_stats_widget()
        container_layout.addWidget(self.quality_stats_widget)
        
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        return widget
    
    def create_charts_tab(self) -> QWidget:
        """グラフタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # グラフコンテナ
        self.chart_container = QLabel("Loading charts...")
        self.chart_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_container.setMinimumHeight(400)
        self.chart_container.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border-radius: 5px;
                padding: 20px;
            }
        """)
        
        layout.addWidget(self.chart_container)
        
        # グラフ更新ボタン
        refresh_btn = QPushButton("🔄 Refresh Charts")
        refresh_btn.clicked.connect(self.update_charts)
        layout.addWidget(refresh_btn)
        
        return widget
    
    def create_presets_tab(self) -> QWidget:
        """プリセットタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # プリセット使用頻度ウィジェット
        self.preset_usage_widget = PresetUsageWidget(self.api_base_url)
        layout.addWidget(self.preset_usage_widget)
        
        return widget
    
    def create_summary_widget(self) -> QGroupBox:
        """サマリーウィジェットを作成"""
        group = QGroupBox("Summary")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # メトリクスカード
        self.total_photos_label = self.create_metric_card("Total Photos", "0")
        layout.addWidget(self.total_photos_label, 0, 0)
        
        self.processed_photos_label = self.create_metric_card("Processed", "0")
        layout.addWidget(self.processed_photos_label, 0, 1)
        
        self.approved_photos_label = self.create_metric_card("Approved", "0")
        layout.addWidget(self.approved_photos_label, 0, 2)
        
        self.success_rate_label = self.create_metric_card("Success Rate", "0%")
        layout.addWidget(self.success_rate_label, 1, 0)
        
        self.avg_time_label = self.create_metric_card("Avg Time", "0s")
        layout.addWidget(self.avg_time_label, 1, 1)
        
        self.time_saved_label = self.create_metric_card("Time Saved", "0h")
        layout.addWidget(self.time_saved_label, 1, 2)
        
        return group
    
    def create_processing_stats_widget(self) -> QGroupBox:
        """処理統計ウィジェットを作成"""
        group = QGroupBox("Processing Statistics")
        layout = QVBoxLayout(group)
        
        self.processing_stats_text = QLabel("Loading...")
        self.processing_stats_text.setWordWrap(True)
        layout.addWidget(self.processing_stats_text)
        
        return group
    
    def create_quality_stats_widget(self) -> QGroupBox:
        """品質統計ウィジェットを作成"""
        group = QGroupBox("Quality Statistics")
        layout = QVBoxLayout(group)
        
        self.quality_stats_text = QLabel("Loading...")
        self.quality_stats_text.setWordWrap(True)
        layout.addWidget(self.quality_stats_text)
        
        return group
    
    def create_metric_card(self, title: str, value: str) -> QFrame:
        """メトリクスカードを作成"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        layout.addWidget(value_label)
        
        # カードにvalue_labelへの参照を保存
        card.value_label = value_label
        
        return card
    
    def on_period_changed(self, period_text: str):
        """期間変更時の処理"""
        self.current_period = period_text.lower()
        self.update_statistics()
    
    def update_statistics(self):
        """統計情報を更新"""
        try:
            # 期間に応じたエンドポイントを選択
            if self.current_period == "daily":
                endpoint = "/statistics/daily"
            elif self.current_period == "weekly":
                endpoint = "/statistics/weekly"
            else:
                endpoint = "/statistics/monthly"
            
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                stats = response.json()
                self.display_statistics(stats)
            else:
                self.show_error("Failed to load statistics")
                
        except Exception as e:
            self.show_error(f"Error loading statistics: {e}")
    
    def display_statistics(self, stats: Dict):
        """統計情報を表示"""
        # 期間に応じたデータを取得
        period_key = self.current_period.replace("ly", "")  # daily -> day
        if period_key == "dai":
            period_key = "today"
        
        period_stats = stats.get(period_key, stats.get('today', {}))
        
        # サマリーカードを更新
        total_imported = period_stats.get('total_imported', 0)
        total_processed = period_stats.get('total_processed', 0)
        total_approved = period_stats.get('total_approved', 0)
        success_rate = period_stats.get('success_rate', 0) * 100
        avg_time = period_stats.get('avg_processing_time', 0)
        
        # 時間節約計算（手動選別と比較）
        manual_time_per_photo = 30  # 秒
        auto_time_per_photo = avg_time
        time_saved_seconds = total_processed * (manual_time_per_photo - auto_time_per_photo)
        time_saved_hours = time_saved_seconds / 3600
        
        self.total_photos_label.value_label.setText(str(total_imported))
        self.processed_photos_label.value_label.setText(str(total_processed))
        self.approved_photos_label.value_label.setText(str(total_approved))
        self.success_rate_label.value_label.setText(f"{success_rate:.1f}%")
        self.avg_time_label.value_label.setText(f"{avg_time:.1f}s")
        self.time_saved_label.value_label.setText(f"{time_saved_hours:.1f}h")
        
        # 処理統計を更新
        self.update_processing_stats(period_stats)
        
        # 品質統計を更新
        self.update_quality_stats(period_stats)
    
    def update_processing_stats(self, stats: Dict):
        """処理統計を更新"""
        total_imported = stats.get('total_imported', 0)
        total_selected = stats.get('total_selected', 0)
        total_processed = stats.get('total_processed', 0)
        total_exported = stats.get('total_exported', 0)
        
        selection_rate = (total_selected / total_imported * 100) if total_imported > 0 else 0
        processing_rate = (total_processed / total_selected * 100) if total_selected > 0 else 0
        export_rate = (total_exported / total_processed * 100) if total_processed > 0 else 0
        
        text = f"""
        <b>Processing Pipeline:</b><br>
        • Imported: {total_imported} photos<br>
        • Selected: {total_selected} photos ({selection_rate:.1f}%)<br>
        • Processed: {total_processed} photos ({processing_rate:.1f}%)<br>
        • Exported: {total_exported} photos ({export_rate:.1f}%)<br>
        """
        
        self.processing_stats_text.setText(text)
    
    def update_quality_stats(self, stats: Dict):
        """品質統計を更新"""
        # 仮のデータ（実際はAPIから取得）
        avg_ai_score = stats.get('avg_ai_score', 3.5)
        avg_focus_score = stats.get('avg_focus_score', 4.2)
        avg_exposure_score = stats.get('avg_exposure_score', 4.0)
        avg_composition_score = stats.get('avg_composition_score', 3.8)
        
        text = f"""
        <b>Quality Metrics:</b><br>
        • Average AI Score: {avg_ai_score:.1f} / 5.0<br>
        • Average Focus Score: {avg_focus_score:.1f} / 5.0<br>
        • Average Exposure Score: {avg_exposure_score:.1f} / 5.0<br>
        • Average Composition Score: {avg_composition_score:.1f} / 5.0<br>
        """
        
        self.quality_stats_text.setText(text)
    
    def update_charts(self):
        """グラフを更新"""
        try:
            # matplotlibを使用してグラフを生成
            import matplotlib
            matplotlib.use('Agg')  # GUIバックエンドを使用しない
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            
            # 統計データを取得
            response = requests.get(
                f"{self.api_base_url}/statistics/{self.current_period}",
                timeout=5
            )
            
            if response.status_code != 200:
                self.chart_container.setText("Failed to load chart data")
                return
            
            stats = response.json()
            
            # グラフを作成
            fig = Figure(figsize=(10, 6), facecolor='#1e1e1e')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#2b2b2b')
            
            # データを準備（例：日次処理数）
            dates = []
            processed_counts = []
            
            # 過去7日間のデータを生成（実際はAPIから取得）
            for i in range(7):
                date = datetime.now() - timedelta(days=6-i)
                dates.append(date.strftime('%m/%d'))
                # 仮のデータ
                processed_counts.append(50 + i * 10)
            
            # 棒グラフを描画
            ax.bar(dates, processed_counts, color='#4CAF50', alpha=0.8)
            ax.set_xlabel('Date', color='white')
            ax.set_ylabel('Photos Processed', color='white')
            ax.set_title('Processing Activity', color='white', fontsize=14, fontweight='bold')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.2)
            
            # グラフを画像として保存
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # QPixmapに変換して表示
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self.chart_container.setPixmap(pixmap)
            
            plt.close(fig)
            
        except ImportError:
            self.chart_container.setText(
                "Matplotlib not installed.\n"
                "Install with: pip install matplotlib"
            )
        except Exception as e:
            self.chart_container.setText(f"Error generating charts: {e}")
    
    def export_to_csv(self):
        """CSV形式でエクスポート"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Statistics to CSV",
                f"statistics_{self.current_period}_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # 統計データを取得
            response = requests.get(
                f"{self.api_base_url}/statistics/{self.current_period}",
                timeout=5
            )
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Export Failed", "Failed to retrieve statistics data")
                return
            
            stats = response.json()
            
            # CSVに書き込み
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # ヘッダー
                writer.writerow(['Metric', 'Value'])
                writer.writerow([])
                
                # サマリー
                writer.writerow(['Summary', ''])
                period_key = 'today' if self.current_period == 'daily' else self.current_period.replace('ly', '')
                period_stats = stats.get(period_key, stats.get('today', {}))
                
                writer.writerow(['Total Imported', period_stats.get('total_imported', 0)])
                writer.writerow(['Total Processed', period_stats.get('total_processed', 0)])
                writer.writerow(['Total Approved', period_stats.get('total_approved', 0)])
                writer.writerow(['Success Rate', f"{period_stats.get('success_rate', 0) * 100:.1f}%"])
                writer.writerow(['Avg Processing Time', f"{period_stats.get('avg_processing_time', 0):.1f}s"])
                writer.writerow([])
                
                # プリセット使用統計
                writer.writerow(['Preset Usage', ''])
                preset_usage = stats.get('preset_usage', {})
                for preset_name, count in preset_usage.items():
                    writer.writerow([preset_name, count])
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Statistics exported to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export statistics:\n{str(e)}"
            )
    
    def export_to_pdf(self):
        """PDF形式でエクスポート"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Statistics to PDF",
                f"statistics_{self.current_period}_{datetime.now().strftime('%Y%m%d')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # reportlabを使用してPDFを生成
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.units import inch
                
                # PDFドキュメントを作成
                doc = SimpleDocTemplate(file_path, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                # タイトル
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor('#1976D2'),
                    spaceAfter=30
                )
                title = Paragraph(f"Junmai AutoDev - {self.current_period.capitalize()} Statistics", title_style)
                elements.append(title)
                elements.append(Spacer(1, 0.2*inch))
                
                # 統計データを取得
                response = requests.get(
                    f"{self.api_base_url}/statistics/{self.current_period}",
                    timeout=5
                )
                
                if response.status_code != 200:
                    QMessageBox.warning(self, "Export Failed", "Failed to retrieve statistics data")
                    return
                
                stats = response.json()
                period_key = 'today' if self.current_period == 'daily' else self.current_period.replace('ly', '')
                period_stats = stats.get(period_key, stats.get('today', {}))
                
                # サマリーテーブル
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Imported', str(period_stats.get('total_imported', 0))],
                    ['Total Processed', str(period_stats.get('total_processed', 0))],
                    ['Total Approved', str(period_stats.get('total_approved', 0))],
                    ['Success Rate', f"{period_stats.get('success_rate', 0) * 100:.1f}%"],
                    ['Avg Processing Time', f"{period_stats.get('avg_processing_time', 0):.1f}s"]
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # プリセット使用統計
                preset_title = Paragraph("Preset Usage Statistics", styles['Heading2'])
                elements.append(preset_title)
                elements.append(Spacer(1, 0.1*inch))
                
                preset_usage = stats.get('preset_usage', {})
                if preset_usage:
                    preset_data = [['Preset Name', 'Usage Count']]
                    for preset_name, count in preset_usage.items():
                        preset_data.append([preset_name, str(count)])
                    
                    preset_table = Table(preset_data, colWidths=[3*inch, 2*inch])
                    preset_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    elements.append(preset_table)
                
                # PDFを生成
                doc.build(elements)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Statistics exported to:\n{file_path}"
                )
                
            except ImportError:
                QMessageBox.warning(
                    self,
                    "PDF Export Not Available",
                    "ReportLab library is not installed.\n"
                    "Install with: pip install reportlab"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export statistics:\n{str(e)}"
            )
    
    def show_error(self, message: str):
        """エラーメッセージを表示"""
        self.total_photos_label.value_label.setText("--")
        self.processed_photos_label.value_label.setText("--")
        self.approved_photos_label.value_label.setText("--")
        self.success_rate_label.value_label.setText("--")
        self.avg_time_label.value_label.setText("--")
        self.time_saved_label.value_label.setText("--")
        
        self.processing_stats_text.setText(f"<b>Error:</b> {message}")
        self.quality_stats_text.setText(f"<b>Error:</b> {message}")



class PresetUsageWidget(QWidget):
    """
    プリセット使用頻度表示ウィジェット
    
    Requirements: 15.3 - プリセット使用頻度の可視化
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
        
        # 定期更新タイマー（60秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_preset_usage)
        self.update_timer.start(60000)
        
        # 初回更新
        self.update_preset_usage()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # タイトル
        title = QLabel("Preset Usage Frequency")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # プリセットコンテナ
        self.preset_container = QWidget()
        self.preset_layout = QVBoxLayout(self.preset_container)
        self.preset_layout.setSpacing(10)
        self.preset_layout.addStretch()
        
        scroll.setWidget(self.preset_container)
        layout.addWidget(scroll)
        
        # グラフ表示ボタン
        self.show_chart_btn = QPushButton("📊 Show Chart")
        self.show_chart_btn.clicked.connect(self.show_preset_chart)
        layout.addWidget(self.show_chart_btn)
    
    def update_preset_usage(self):
        """プリセット使用頻度を更新"""
        try:
            response = requests.get(
                f"{self.api_base_url}/statistics/presets",
                timeout=5
            )
            
            if response.status_code == 200:
                preset_data = response.json()
                self.display_preset_usage(preset_data)
            else:
                self.show_error("Failed to load preset usage data")
                
        except Exception as e:
            self.show_error(f"Error: {e}")
    
    def display_preset_usage(self, preset_data: Dict):
        """プリセット使用頻度を表示"""
        # 既存のウィジェットをクリア
        while self.preset_layout.count() > 1:  # Keep stretch
            item = self.preset_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        preset_usage = preset_data.get('preset_usage', {})
        
        if not preset_usage:
            no_data = QLabel("No preset usage data available")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setStyleSheet("color: #888;")
            self.preset_layout.insertWidget(0, no_data)
            return
        
        # 使用回数でソート
        sorted_presets = sorted(
            preset_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 合計使用回数を計算
        total_usage = sum(preset_usage.values())
        
        # 各プリセットの使用頻度を表示
        for preset_name, count in sorted_presets:
            preset_widget = self.create_preset_usage_widget(
                preset_name,
                count,
                total_usage
            )
            self.preset_layout.insertWidget(
                self.preset_layout.count() - 1,
                preset_widget
            )
    
    def create_preset_usage_widget(
        self,
        preset_name: str,
        count: int,
        total: int
    ) -> QWidget:
        """個別プリセット使用頻度ウィジェットを作成"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # プリセット名と使用回数
        header_layout = QHBoxLayout()
        
        name_label = QLabel(preset_name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        count_label = QLabel(f"{count} times")
        header_layout.addWidget(count_label)
        
        layout.addLayout(header_layout)
        
        # 使用率バー
        percentage = (count / total * 100) if total > 0 else 0
        
        from PyQt6.QtWidgets import QProgressBar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(percentage))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{percentage:.1f}%")
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        layout.addWidget(progress_bar)
        
        return widget
    
    def show_preset_chart(self):
        """プリセット使用頻度のグラフを表示"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            
            # プリセットデータを取得
            response = requests.get(
                f"{self.api_base_url}/statistics/presets",
                timeout=5
            )
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Chart Error", "Failed to load preset data")
                return
            
            preset_data = response.json()
            preset_usage = preset_data.get('preset_usage', {})
            
            if not preset_usage:
                QMessageBox.information(self, "No Data", "No preset usage data available")
                return
            
            # グラフを作成
            fig = Figure(figsize=(10, 6), facecolor='#1e1e1e')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#2b2b2b')
            
            # データを準備
            presets = list(preset_usage.keys())
            counts = list(preset_usage.values())
            
            # 円グラフを描画
            colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336', '#9C27B0', '#00BCD4']
            ax.pie(
                counts,
                labels=presets,
                autopct='%1.1f%%',
                colors=colors[:len(presets)],
                textprops={'color': 'white'}
            )
            ax.set_title('Preset Usage Distribution', color='white', fontsize=14, fontweight='bold')
            
            # グラフを画像として保存
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # 新しいウィンドウで表示
            chart_dialog = QMessageBox(self)
            chart_dialog.setWindowTitle("Preset Usage Chart")
            
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            chart_dialog.setIconPixmap(pixmap)
            chart_dialog.setText("Preset Usage Distribution")
            chart_dialog.exec()
            
            plt.close(fig)
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Chart Not Available",
                "Matplotlib is not installed.\n"
                "Install with: pip install matplotlib"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Chart Error",
                f"Failed to generate chart:\n{str(e)}"
            )
    
    def show_error(self, message: str):
        """エラーメッセージを表示"""
        # 既存のウィジェットをクリア
        while self.preset_layout.count() > 1:
            item = self.preset_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel(f"<b>Error:</b> {message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #F44336;")
        self.preset_layout.insertWidget(0, error_label)
