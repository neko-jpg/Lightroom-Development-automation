"""
Email Notification System for Junmai AutoDev

Provides email notifications with:
- SMTP configuration management
- Email templates for different notification types
- Batch notification support
- HTML and plain text email support

Requirements: 8.1, 8.2
"""

import logging
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class EmailNotificationType(Enum):
    """Email notification types"""
    PROCESSING_COMPLETE = "processing_complete"
    APPROVAL_REQUIRED = "approval_required"
    ERROR = "error"
    EXPORT_COMPLETE = "export_complete"
    BATCH_COMPLETE = "batch_complete"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"


class EmailTemplate:
    """Email template manager"""
    
    @staticmethod
    def get_template(notification_type: EmailNotificationType) -> Dict[str, str]:
        """
        Get email template for notification type
        
        Args:
            notification_type: Type of notification
            
        Returns:
            Dictionary with 'subject', 'html', and 'text' keys
        """
        templates = {
            EmailNotificationType.PROCESSING_COMPLETE: {
                'subject': '処理完了 - {session_name}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #4CAF50;">✓ 処理完了</h2>
                        <p><strong>{session_name}</strong> の処理が完了しました。</p>
                        <ul>
                            <li>処理枚数: <strong>{photo_count}枚</strong></li>
                            <li>成功率: <strong>{success_rate:.1f}%</strong></li>
                            <li>処理時間: <strong>{processing_time}</strong></li>
                        </ul>
                        <p><a href="{dashboard_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ダッシュボードを開く</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
処理完了

{session_name} の処理が完了しました。

処理枚数: {photo_count}枚
成功率: {success_rate:.1f}%
処理時間: {processing_time}

ダッシュボード: {dashboard_url}
                '''
            },
            EmailNotificationType.APPROVAL_REQUIRED: {
                'subject': '承認待ち - {pending_count}枚',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #FF9800;">📋 承認待ち</h2>
                        <p><strong>{pending_count}枚</strong>の写真が承認待ちです。</p>
                        <p>以下のセッションで承認が必要です:</p>
                        <ul>
                            {session_list}
                        </ul>
                        <p><a href="{approval_url}" style="background-color: #FF9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">承認キューを開く</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
承認待ち

{pending_count}枚の写真が承認待ちです。

セッション:
{session_list}

承認キュー: {approval_url}
                '''
            },
            EmailNotificationType.ERROR: {
                'subject': 'エラー発生 - {error_type}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #F44336;">⚠ エラー発生</h2>
                        <p><strong>{error_message}</strong></p>
                        <div style="background-color: #ffebee; padding: 15px; border-left: 4px solid #F44336; margin: 15px 0;">
                            <p><strong>詳細:</strong></p>
                            <pre style="white-space: pre-wrap; word-wrap: break-word;">{error_details}</pre>
                        </div>
                        <p>発生時刻: {timestamp}</p>
                        <p><a href="{dashboard_url}" style="background-color: #F44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ダッシュボードを確認</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
エラー発生

{error_message}

詳細:
{error_details}

発生時刻: {timestamp}

ダッシュボード: {dashboard_url}
                '''
            },
            EmailNotificationType.EXPORT_COMPLETE: {
                'subject': '書き出し完了 - {export_preset}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #2196F3;">📤 書き出し完了</h2>
                        <p><strong>{export_preset}</strong> プリセットで書き出しが完了しました。</p>
                        <ul>
                            <li>書き出し枚数: <strong>{photo_count}枚</strong></li>
                            <li>保存先: <code>{destination}</code></li>
                        </ul>
                        <p><a href="{dashboard_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ダッシュボードを開く</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
書き出し完了

{export_preset} プリセットで書き出しが完了しました。

書き出し枚数: {photo_count}枚
保存先: {destination}

ダッシュボード: {dashboard_url}
                '''
            },
            EmailNotificationType.BATCH_COMPLETE: {
                'subject': 'バッチ処理完了 - {batch_name}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #9C27B0;">🎯 バッチ処理完了</h2>
                        <p><strong>{batch_name}</strong> のバッチ処理が完了しました。</p>
                        <ul>
                            <li>処理枚数: <strong>{total_photos}枚</strong></li>
                            <li>処理時間: <strong>{processing_time}</strong></li>
                            <li>平均処理時間: <strong>{avg_time_per_photo}</strong></li>
                        </ul>
                        <p><a href="{dashboard_url}" style="background-color: #9C27B0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ダッシュボードを開く</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
バッチ処理完了

{batch_name} のバッチ処理が完了しました。

処理枚数: {total_photos}枚
処理時間: {processing_time}
平均処理時間: {avg_time_per_photo}

ダッシュボード: {dashboard_url}
                '''
            },
            EmailNotificationType.DAILY_SUMMARY: {
                'subject': '日次レポート - {date}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #607D8B;">📊 日次レポート</h2>
                        <p><strong>{date}</strong> の処理サマリー</p>
                        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                            <tr style="background-color: #f5f5f5;">
                                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">項目</th>
                                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">値</th>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">取り込み枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_imported}</strong></td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="border: 1px solid #ddd; padding: 12px;">選別枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_selected}</strong></td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">現像枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_processed}</strong></td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="border: 1px solid #ddd; padding: 12px;">書き出し枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_exported}</strong></td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">平均処理時間</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{avg_processing_time}</strong></td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="border: 1px solid #ddd; padding: 12px;">成功率</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{success_rate:.1f}%</strong></td>
                            </tr>
                        </table>
                        <p><a href="{dashboard_url}" style="background-color: #607D8B; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">詳細レポートを見る</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
日次レポート - {date}

取り込み枚数: {total_imported}
選別枚数: {total_selected}
現像枚数: {total_processed}
書き出し枚数: {total_exported}
平均処理時間: {avg_processing_time}
成功率: {success_rate:.1f}%

詳細レポート: {dashboard_url}
                '''
            },
            EmailNotificationType.WEEKLY_SUMMARY: {
                'subject': '週次レポート - {week_range}',
                'html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #3F51B5;">📈 週次レポート</h2>
                        <p><strong>{week_range}</strong> の処理サマリー</p>
                        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                            <tr style="background-color: #f5f5f5;">
                                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">項目</th>
                                <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">値</th>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">総取り込み枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_imported}</strong></td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="border: 1px solid #ddd; padding: 12px;">総現像枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_processed}</strong></td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">総書き出し枚数</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{total_exported}</strong></td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="border: 1px solid #ddd; padding: 12px;">平均成功率</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{avg_success_rate:.1f}%</strong></td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 12px;">最も使用されたプリセット</td>
                                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;"><strong>{top_preset}</strong></td>
                            </tr>
                        </table>
                        <h3>日別推移</h3>
                        <ul>
                            {daily_breakdown}
                        </ul>
                        <p><a href="{dashboard_url}" style="background-color: #3F51B5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">詳細レポートを見る</a></p>
                    </body>
                    </html>
                ''',
                'text': '''
週次レポート - {week_range}

総取り込み枚数: {total_imported}
総現像枚数: {total_processed}
総書き出し枚数: {total_exported}
平均成功率: {avg_success_rate:.1f}%
最も使用されたプリセット: {top_preset}

日別推移:
{daily_breakdown}

詳細レポート: {dashboard_url}
                '''
            }
        }
        
        return templates.get(notification_type, {
            'subject': 'Junmai AutoDev 通知',
            'html': '<html><body><p>{message}</p></body></html>',
            'text': '{message}'
        })


class SMTPConfig:
    """SMTP configuration manager"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize SMTP configuration
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            base_dir = Path(__file__).parent
            config_file = base_dir / "config" / "email_config.json"
        
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load SMTP configuration from file"""
        if not self.config_file.exists():
            self.config = self._get_default_config()
            self._save_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("SMTP configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load SMTP configuration: {e}")
            self.config = self._get_default_config()
    
    def _save_config(self) -> None:
        """Save SMTP configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("SMTP configuration saved")
        except Exception as e:
            logger.error(f"Failed to save SMTP configuration: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default SMTP configuration"""
        return {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'username': '',
            'password': '',
            'from_address': '',
            'from_name': 'Junmai AutoDev',
            'to_addresses': [],
            'batch_notifications': {
                'enabled': True,
                'interval_minutes': 60,
                'min_notifications': 3
            },
            'notification_types': {
                'processing_complete': True,
                'approval_required': True,
                'error': True,
                'export_complete': False,
                'batch_complete': True,
                'daily_summary': True,
                'weekly_summary': True
            }
        }
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update SMTP configuration
        
        Args:
            config_dict: Configuration dictionary
        """
        self.config.update(config_dict)
        self._save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled"""
        return self.config.get('enabled', False)
    
    def is_type_enabled(self, notification_type: EmailNotificationType) -> bool:
        """
        Check if specific notification type is enabled
        
        Args:
            notification_type: Type of notification
            
        Returns:
            True if notification type is enabled
        """
        types = self.config.get('notification_types', {})
        return types.get(notification_type.value, True)


class BatchNotificationManager:
    """Manages batch notification buffering"""
    
    def __init__(self, config: SMTPConfig):
        """
        Initialize batch notification manager
        
        Args:
            config: SMTP configuration
        """
        self.config = config
        self.buffer: List[Dict[str, Any]] = []
        self.last_send_time = datetime.now()
    
    def add(self, notification: Dict[str, Any]) -> bool:
        """
        Add notification to buffer
        
        Args:
            notification: Notification data
            
        Returns:
            True if buffer should be flushed
        """
        self.buffer.append(notification)
        
        batch_config = self.config.get('batch_notifications', {})
        if not batch_config.get('enabled', True):
            return True
        
        interval_minutes = batch_config.get('interval_minutes', 60)
        min_notifications = batch_config.get('min_notifications', 3)
        
        # Check if we should flush
        time_elapsed = (datetime.now() - self.last_send_time).total_seconds() / 60
        
        if len(self.buffer) >= min_notifications or time_elapsed >= interval_minutes:
            return True
        
        return False
    
    def get_and_clear(self) -> List[Dict[str, Any]]:
        """
        Get buffered notifications and clear buffer
        
        Returns:
            List of buffered notifications
        """
        notifications = self.buffer.copy()
        self.buffer.clear()
        self.last_send_time = datetime.now()
        return notifications
    
    def clear(self) -> None:
        """Clear notification buffer"""
        self.buffer.clear()
        self.last_send_time = datetime.now()


class EmailNotifier:
    """
    Email notification manager
    
    Provides email notifications with SMTP support and batch processing
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize email notifier
        
        Args:
            config_file: Path to configuration file
        """
        self.config = SMTPConfig(config_file)
        self.batch_manager = BatchNotificationManager(self.config)
        self.template = EmailTemplate()
    
    def send(
        self,
        to_addresses: Optional[List[str]],
        subject: str,
        html_body: str,
        text_body: str,
        notification_type: EmailNotificationType = EmailNotificationType.PROCESSING_COMPLETE,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_addresses: List of recipient email addresses (None = use config)
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            notification_type: Type of notification
            attachments: List of file paths to attach
            
        Returns:
            True if email was sent successfully
        """
        if not self.config.is_enabled():
            logger.warning("Email notifications are disabled")
            return False
        
        if not self.config.is_type_enabled(notification_type):
            logger.info(f"Email notification type {notification_type.value} is disabled")
            return False
        
        # Use configured addresses if not specified
        if to_addresses is None:
            to_addresses = self.config.get('to_addresses', [])
        
        if not to_addresses:
            logger.warning("No recipient email addresses configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.get('from_name')} <{self.config.get('from_address')}>"
            msg['To'] = ', '.join(to_addresses)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach text and HTML parts
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Attach files if provided
            if attachments:
                for attachment_path in attachments:
                    if attachment_path.exists():
                        with open(attachment_path, 'rb') as f:
                            img = MIMEImage(f.read())
                            img.add_header('Content-Disposition', 'attachment', filename=attachment_path.name)
                            msg.attach(img)
            
            # Send email
            smtp_server = self.config.get('smtp_server')
            smtp_port = self.config.get('smtp_port')
            use_tls = self.config.get('use_tls', True)
            use_ssl = self.config.get('use_ssl', False)
            username = self.config.get('username')
            password = self.config.get('password')
            
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()
            
            if username and password:
                server.login(username, password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_with_template(
        self,
        notification_type: EmailNotificationType,
        data: Dict[str, Any],
        to_addresses: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using template
        
        Args:
            notification_type: Type of notification
            data: Template data dictionary
            to_addresses: List of recipient email addresses
            
        Returns:
            True if email was sent successfully
        """
        template = self.template.get_template(notification_type)
        
        # Add default dashboard URL if not provided
        if 'dashboard_url' not in data:
            data['dashboard_url'] = 'http://localhost:5100'
        
        # Format template
        try:
            subject = template['subject'].format(**data)
            html_body = template['html'].format(**data)
            text_body = template['text'].format(**data)
        except KeyError as e:
            logger.error(f"Missing template data key: {e}")
            return False
        
        return self.send(
            to_addresses=to_addresses,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            notification_type=notification_type
        )

    def send_processing_complete(
        self,
        session_name: str,
        photo_count: int,
        success_rate: float,
        processing_time: str
    ) -> bool:
        """
        Send processing complete notification
        
        Args:
            session_name: Name of the session
            photo_count: Number of photos processed
            success_rate: Success rate percentage
            processing_time: Processing time string (e.g., "2h 15m")
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_template(
            EmailNotificationType.PROCESSING_COMPLETE,
            {
                'session_name': session_name,
                'photo_count': photo_count,
                'success_rate': success_rate,
                'processing_time': processing_time
            }
        )
    
    def send_approval_required(
        self,
        pending_count: int,
        sessions: List[Dict[str, Any]]
    ) -> bool:
        """
        Send approval required notification
        
        Args:
            pending_count: Number of photos pending approval
            sessions: List of session dictionaries with 'name' and 'count' keys
            
        Returns:
            True if notification was sent successfully
        """
        # Format session list
        session_list_html = '\n'.join([
            f"<li>{s['name']}: {s['count']}枚</li>"
            for s in sessions
        ])
        session_list_text = '\n'.join([
            f"- {s['name']}: {s['count']}枚"
            for s in sessions
        ])
        
        return self.send_with_template(
            EmailNotificationType.APPROVAL_REQUIRED,
            {
                'pending_count': pending_count,
                'session_list': session_list_html,
                'approval_url': 'http://localhost:5100/approval'
            }
        )
    
    def send_error(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Send error notification
        
        Args:
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_template(
            EmailNotificationType.ERROR,
            {
                'error_type': error_type,
                'error_message': error_message,
                'error_details': error_details or 'No additional details',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )
    
    def send_export_complete(
        self,
        export_preset: str,
        photo_count: int,
        destination: str
    ) -> bool:
        """
        Send export complete notification
        
        Args:
            export_preset: Export preset name
            photo_count: Number of photos exported
            destination: Export destination path
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_template(
            EmailNotificationType.EXPORT_COMPLETE,
            {
                'export_preset': export_preset,
                'photo_count': photo_count,
                'destination': destination
            }
        )
    
    def send_batch_complete(
        self,
        batch_name: str,
        total_photos: int,
        processing_time: str,
        avg_time_per_photo: str
    ) -> bool:
        """
        Send batch complete notification
        
        Args:
            batch_name: Batch name
            total_photos: Total number of photos in batch
            processing_time: Total processing time string
            avg_time_per_photo: Average time per photo string
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_template(
            EmailNotificationType.BATCH_COMPLETE,
            {
                'batch_name': batch_name,
                'total_photos': total_photos,
                'processing_time': processing_time,
                'avg_time_per_photo': avg_time_per_photo
            }
        )
    
    def send_daily_summary(
        self,
        date: str,
        total_imported: int,
        total_selected: int,
        total_processed: int,
        total_exported: int,
        avg_processing_time: str,
        success_rate: float
    ) -> bool:
        """
        Send daily summary notification
        
        Args:
            date: Date string
            total_imported: Total imported photos
            total_selected: Total selected photos
            total_processed: Total processed photos
            total_exported: Total exported photos
            avg_processing_time: Average processing time string
            success_rate: Success rate percentage
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_template(
            EmailNotificationType.DAILY_SUMMARY,
            {
                'date': date,
                'total_imported': total_imported,
                'total_selected': total_selected,
                'total_processed': total_processed,
                'total_exported': total_exported,
                'avg_processing_time': avg_processing_time,
                'success_rate': success_rate
            }
        )
    
    def send_weekly_summary(
        self,
        week_range: str,
        total_imported: int,
        total_processed: int,
        total_exported: int,
        avg_success_rate: float,
        top_preset: str,
        daily_breakdown: List[Dict[str, Any]]
    ) -> bool:
        """
        Send weekly summary notification
        
        Args:
            week_range: Week range string (e.g., "2025-11-01 ~ 2025-11-07")
            total_imported: Total imported photos
            total_processed: Total processed photos
            total_exported: Total exported photos
            avg_success_rate: Average success rate percentage
            top_preset: Most used preset name
            daily_breakdown: List of daily statistics
            
        Returns:
            True if notification was sent successfully
        """
        # Format daily breakdown
        breakdown_html = '\n'.join([
            f"<li>{day['date']}: {day['processed']}枚処理</li>"
            for day in daily_breakdown
        ])
        breakdown_text = '\n'.join([
            f"- {day['date']}: {day['processed']}枚処理"
            for day in daily_breakdown
        ])
        
        return self.send_with_template(
            EmailNotificationType.WEEKLY_SUMMARY,
            {
                'week_range': week_range,
                'total_imported': total_imported,
                'total_processed': total_processed,
                'total_exported': total_exported,
                'avg_success_rate': avg_success_rate,
                'top_preset': top_preset,
                'daily_breakdown': breakdown_html
            }
        )
    
    def add_to_batch(self, notification_data: Dict[str, Any]) -> bool:
        """
        Add notification to batch buffer
        
        Args:
            notification_data: Notification data dictionary
            
        Returns:
            True if batch should be sent now
        """
        return self.batch_manager.add(notification_data)
    
    def send_batch(self) -> bool:
        """
        Send all buffered notifications as a batch
        
        Returns:
            True if batch was sent successfully
        """
        notifications = self.batch_manager.get_and_clear()
        
        if not notifications:
            return True
        
        # Group notifications by type
        grouped = {}
        for notif in notifications:
            notif_type = notif.get('type', 'general')
            if notif_type not in grouped:
                grouped[notif_type] = []
            grouped[notif_type].append(notif)
        
        # Create batch summary
        summary_html = '<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">'
        summary_html += '<h2>通知サマリー</h2>'
        summary_html += f'<p>{len(notifications)}件の通知があります。</p>'
        
        summary_text = '通知サマリー\n\n'
        summary_text += f'{len(notifications)}件の通知があります。\n\n'
        
        for notif_type, notifs in grouped.items():
            summary_html += f'<h3>{notif_type} ({len(notifs)}件)</h3><ul>'
            summary_text += f'{notif_type} ({len(notifs)}件):\n'
            
            for notif in notifs:
                summary_html += f"<li>{notif.get('message', '')}</li>"
                summary_text += f"- {notif.get('message', '')}\n"
            
            summary_html += '</ul>'
            summary_text += '\n'
        
        summary_html += '</body></html>'
        
        return self.send(
            to_addresses=None,
            subject=f'バッチ通知 - {len(notifications)}件',
            html_body=summary_html,
            text_body=summary_text,
            notification_type=EmailNotificationType.BATCH_COMPLETE
        )
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update SMTP configuration
        
        Args:
            config_dict: Configuration dictionary
        """
        self.config.update(config_dict)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current SMTP configuration
        
        Returns:
            Configuration dictionary
        """
        return self.config.config.copy()
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            True if connection is successful
        """
        try:
            smtp_server = self.config.get('smtp_server')
            smtp_port = self.config.get('smtp_port')
            use_tls = self.config.get('use_tls', True)
            use_ssl = self.config.get('use_ssl', False)
            username = self.config.get('username')
            password = self.config.get('password')
            
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                if use_tls:
                    server.starttls()
            
            if username and password:
                server.login(username, password)
            
            server.quit()
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False


# Singleton instance
_email_notifier_instance: Optional[EmailNotifier] = None


def get_email_notifier() -> EmailNotifier:
    """
    Get singleton email notifier instance
    
    Returns:
        EmailNotifier instance
    """
    global _email_notifier_instance
    if _email_notifier_instance is None:
        _email_notifier_instance = EmailNotifier()
    return _email_notifier_instance


def send_email_notification(
    notification_type: EmailNotificationType,
    data: Dict[str, Any],
    to_addresses: Optional[List[str]] = None
) -> bool:
    """
    Convenience function to send email notification
    
    Args:
        notification_type: Type of notification
        data: Template data dictionary
        to_addresses: List of recipient email addresses
        
    Returns:
        True if notification was sent successfully
    """
    notifier = get_email_notifier()
    return notifier.send_with_template(notification_type, data, to_addresses)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Testing Email Notifier ===\n")
    
    # Test 1: Initialize notifier
    print("Test 1: Initialize notifier")
    notifier = EmailNotifier()
    print(f"✓ Email notifier initialized")
    print(f"  Enabled: {notifier.config.is_enabled()}")
    
    # Test 2: Get configuration
    print("\nTest 2: Get configuration")
    config = notifier.get_config()
    print(f"✓ Configuration loaded")
    print(f"  SMTP Server: {config.get('smtp_server')}")
    print(f"  SMTP Port: {config.get('smtp_port')}")
    
    # Test 3: Test templates
    print("\nTest 3: Test templates")
    template = EmailTemplate.get_template(EmailNotificationType.PROCESSING_COMPLETE)
    print(f"✓ Template loaded")
    print(f"  Subject: {template['subject']}")
    
    # Test 4: Update configuration (for testing)
    print("\nTest 4: Update configuration")
    notifier.update_config({
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'username': 'test@example.com',
        'password': 'test_password',
        'from_address': 'test@example.com',
        'to_addresses': ['recipient@example.com']
    })
    print("✓ Configuration updated")
    
    # Test 5: Test batch manager
    print("\nTest 5: Test batch manager")
    should_flush = notifier.add_to_batch({
        'type': 'processing_complete',
        'message': 'Test notification 1'
    })
    print(f"✓ Notification added to batch (flush: {should_flush})")
    
    # Test 6: Test connection (will fail without real credentials)
    print("\nTest 6: Test SMTP connection")
    print("⚠ Skipping connection test (requires real SMTP credentials)")
    
    print("\n=== All tests completed! ===")
    print("\nNote: To actually send emails, configure valid SMTP settings in:")
    print(f"  {notifier.config.config_file}")
