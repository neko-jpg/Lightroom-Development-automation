"""
フェイルセーフ機能実装 (Failsafe Feature Implementation)

このモジュールは、中間状態保存、処理再開、自動バックアップ、
クラッシュ後の自動復旧機能を提供します。

Requirements: 14.3, 14.4, 14.5
"""

import os
import json
import shutil
import pickle
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import threading
import time


# ================================================================================
# 状態定義 (State Definitions)
# ================================================================================

class ProcessState(Enum):
    """処理状態の列挙型"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class CheckpointData:
    """チェックポイントデータ"""
    checkpoint_id: str
    operation_id: str
    operation_name: str
    state: ProcessState
    timestamp: str
    progress: float  # 0.0 - 1.0
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'checkpoint_id': self.checkpoint_id,
            'operation_id': self.operation_id,
            'operation_name': self.operation_name,
            'state': self.state.value,
            'timestamp': self.timestamp,
            'progress': self.progress,
            'data': self.data,
            'metadata': self.metadata
        }


@dataclass
class BackupInfo:
    """バックアップ情報"""
    backup_id: str
    source_path: str
    backup_path: str
    timestamp: str
    size_bytes: int
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


# ================================================================================
# フェイルセーフマネージャー (Failsafe Manager)
# ================================================================================

class FailsafeManager:
    """
    フェイルセーフマネージャー
    
    中間状態保存、処理再開、自動バックアップ、クラッシュ復旧を管理します。
    """
    
    def __init__(
        self,
        checkpoint_dir: str = 'data/checkpoints',
        backup_dir: str = 'data/backups',
        auto_backup_interval: int = 300,  # 5分
        max_checkpoints: int = 10,
        max_backups: int = 5
    ):
        """
        Args:
            checkpoint_dir: チェックポイント保存ディレクトリ
            backup_dir: バックアップ保存ディレクトリ
            auto_backup_interval: 自動バックアップ間隔（秒）
            max_checkpoints: 保持する最大チェックポイント数
            max_backups: 保持する最大バックアップ数
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.backup_dir = Path(backup_dir)
        self.auto_backup_interval = auto_backup_interval
        self.max_checkpoints = max_checkpoints
        self.max_backups = max_backups
        
        # ディレクトリを作成
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # ロガーの設定
        self.logger = self._setup_logger()
        
        # チェックポイント管理
        self.checkpoints: Dict[str, CheckpointData] = {}
        self.active_operations: Dict[str, ProcessState] = {}
        
        # バックアップ管理
        self.backups: List[BackupInfo] = []
        self._load_backup_index()
        
        # 自動バックアップスレッド
        self.auto_backup_enabled = False
        self.auto_backup_thread: Optional[threading.Thread] = None
        self._backup_lock = threading.Lock()
        
        # 起動時にクラッシュ復旧をチェック
        self._check_crash_recovery()
    
    def _setup_logger(self) -> logging.Logger:
        """ロガーのセットアップ"""
        logger = logging.getLogger('junmai_autodev.failsafe')
        logger.setLevel(logging.DEBUG)
        
        # ログディレクトリを作成
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイルハンドラー
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'logs/failsafe.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        return logger
    
    # ========================================================================
    # チェックポイント機能 (Checkpoint Functions)
    # ========================================================================
    
    def save_checkpoint(
        self,
        operation_id: str,
        operation_name: str,
        state: ProcessState,
        progress: float,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        チェックポイントを保存
        
        Args:
            operation_id: 操作ID
            operation_name: 操作名
            state: 処理状態
            progress: 進捗（0.0-1.0）
            data: 保存するデータ
            metadata: メタデータ
        
        Returns:
            str: チェックポイントID
        """
        checkpoint_id = self._generate_checkpoint_id(operation_id)
        
        checkpoint = CheckpointData(
            checkpoint_id=checkpoint_id,
            operation_id=operation_id,
            operation_name=operation_name,
            state=state,
            timestamp=datetime.now().isoformat(),
            progress=progress,
            data=data,
            metadata=metadata or {}
        )
        
        # チェックポイントをファイルに保存
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
            
            # メモリにも保存
            self.checkpoints[checkpoint_id] = checkpoint
            self.active_operations[operation_id] = state
            
            self.logger.info(
                f"Checkpoint saved: {checkpoint_id} for operation {operation_name} "
                f"(progress: {progress:.1%})"
            )
            
            # 古いチェックポイントをクリーンアップ
            self._cleanup_old_checkpoints(operation_id)
            
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint {checkpoint_id}: {e}")
            raise
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """
        チェックポイントを読み込み
        
        Args:
            checkpoint_id: チェックポイントID
        
        Returns:
            Optional[CheckpointData]: チェックポイントデータ
        """
        # メモリから取得を試みる
        if checkpoint_id in self.checkpoints:
            return self.checkpoints[checkpoint_id]
        
        # ファイルから読み込み
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            self.logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checkpoint = CheckpointData(
                checkpoint_id=data['checkpoint_id'],
                operation_id=data['operation_id'],
                operation_name=data['operation_name'],
                state=ProcessState(data['state']),
                timestamp=data['timestamp'],
                progress=data['progress'],
                data=data['data'],
                metadata=data.get('metadata', {})
            )
            
            # メモリにキャッシュ
            self.checkpoints[checkpoint_id] = checkpoint
            
            return checkpoint
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    def get_latest_checkpoint(self, operation_id: str) -> Optional[CheckpointData]:
        """
        操作の最新チェックポイントを取得
        
        Args:
            operation_id: 操作ID
        
        Returns:
            Optional[CheckpointData]: 最新のチェックポイント
        """
        # 該当する操作のチェックポイントを検索
        operation_checkpoints = [
            cp for cp in self.checkpoints.values()
            if cp.operation_id == operation_id
        ]
        
        if not operation_checkpoints:
            # ファイルから検索
            operation_checkpoints = self._load_operation_checkpoints(operation_id)
        
        if not operation_checkpoints:
            return None
        
        # タイムスタンプでソートして最新を返す
        operation_checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        return operation_checkpoints[0]
    
    def _load_operation_checkpoints(self, operation_id: str) -> List[CheckpointData]:
        """操作のすべてのチェックポイントを読み込み"""
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob(f"*{operation_id}*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data['operation_id'] == operation_id:
                    checkpoint = CheckpointData(
                        checkpoint_id=data['checkpoint_id'],
                        operation_id=data['operation_id'],
                        operation_name=data['operation_name'],
                        state=ProcessState(data['state']),
                        timestamp=data['timestamp'],
                        progress=data['progress'],
                        data=data['data'],
                        metadata=data.get('metadata', {})
                    )
                    checkpoints.append(checkpoint)
            except Exception as e:
                self.logger.warning(f"Failed to load checkpoint file {checkpoint_file}: {e}")
        
        return checkpoints
    
    def _generate_checkpoint_id(self, operation_id: str) -> str:
        """チェックポイントIDを生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"checkpoint_{operation_id}_{timestamp}"
    
    def _cleanup_old_checkpoints(self, operation_id: str):
        """古いチェックポイントをクリーンアップ"""
        operation_checkpoints = self._load_operation_checkpoints(operation_id)
        
        if len(operation_checkpoints) > self.max_checkpoints:
            # タイムスタンプでソート
            operation_checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 古いものを削除
            for checkpoint in operation_checkpoints[self.max_checkpoints:]:
                checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
                try:
                    checkpoint_file.unlink()
                    if checkpoint.checkpoint_id in self.checkpoints:
                        del self.checkpoints[checkpoint.checkpoint_id]
                    self.logger.debug(f"Deleted old checkpoint: {checkpoint.checkpoint_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete checkpoint {checkpoint.checkpoint_id}: {e}")
    
    # ========================================================================
    # 処理再開機能 (Resume Functions)
    # ========================================================================
    
    def can_resume(self, operation_id: str) -> bool:
        """
        処理が再開可能かチェック
        
        Args:
            operation_id: 操作ID
        
        Returns:
            bool: 再開可能な場合True
        """
        checkpoint = self.get_latest_checkpoint(operation_id)
        
        if checkpoint is None:
            return False
        
        # 完了または失敗状態でない場合は再開可能
        return checkpoint.state not in [ProcessState.COMPLETED, ProcessState.FAILED]
    
    def resume_operation(
        self,
        operation_id: str,
        resume_callback: Callable[[CheckpointData], Any]
    ) -> Any:
        """
        処理を再開
        
        Args:
            operation_id: 操作ID
            resume_callback: 再開時に呼び出すコールバック関数
        
        Returns:
            Any: コールバックの戻り値
        """
        checkpoint = self.get_latest_checkpoint(operation_id)
        
        if checkpoint is None:
            raise ValueError(f"No checkpoint found for operation: {operation_id}")
        
        if not self.can_resume(operation_id):
            raise ValueError(
                f"Operation {operation_id} cannot be resumed (state: {checkpoint.state.value})"
            )
        
        self.logger.info(
            f"Resuming operation {checkpoint.operation_name} from checkpoint "
            f"{checkpoint.checkpoint_id} (progress: {checkpoint.progress:.1%})"
        )
        
        # 状態を復旧中に更新
        self.save_checkpoint(
            operation_id=operation_id,
            operation_name=checkpoint.operation_name,
            state=ProcessState.RECOVERING,
            progress=checkpoint.progress,
            data=checkpoint.data,
            metadata=checkpoint.metadata
        )
        
        try:
            # コールバックを実行
            result = resume_callback(checkpoint)
            
            # 成功したら完了状態に更新
            self.save_checkpoint(
                operation_id=operation_id,
                operation_name=checkpoint.operation_name,
                state=ProcessState.COMPLETED,
                progress=1.0,
                data=checkpoint.data,
                metadata=checkpoint.metadata
            )
            
            return result
            
        except Exception as e:
            # 失敗したら失敗状態に更新
            self.save_checkpoint(
                operation_id=operation_id,
                operation_name=checkpoint.operation_name,
                state=ProcessState.FAILED,
                progress=checkpoint.progress,
                data=checkpoint.data,
                metadata={'error': str(e)}
            )
            raise
    
    # ========================================================================
    # バックアップ機能 (Backup Functions)
    # ========================================================================
    
    def create_backup(
        self,
        source_path: str,
        backup_name: Optional[str] = None
    ) -> BackupInfo:
        """
        バックアップを作成
        
        Args:
            source_path: バックアップ元のパス
            backup_name: バックアップ名（Noneの場合は自動生成）
        
        Returns:
            BackupInfo: バックアップ情報
        """
        source = Path(source_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        # バックアップ名を生成
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source.stem}_backup_{timestamp}{source.suffix}"
        
        backup_path = self.backup_dir / backup_name
        
        with self._backup_lock:
            try:
                # ファイルまたはディレクトリをコピー
                if source.is_file():
                    shutil.copy2(source, backup_path)
                else:
                    shutil.copytree(source, backup_path)
                
                # チェックサムを計算
                checksum = self._calculate_checksum(backup_path)
                
                # バックアップ情報を作成
                backup_info = BackupInfo(
                    backup_id=self._generate_backup_id(),
                    source_path=str(source),
                    backup_path=str(backup_path),
                    timestamp=datetime.now().isoformat(),
                    size_bytes=self._get_size(backup_path),
                    checksum=checksum
                )
                
                # バックアップリストに追加
                self.backups.append(backup_info)
                self._save_backup_index()
                
                self.logger.info(f"Backup created: {backup_name} ({backup_info.size_bytes} bytes)")
                
                # 古いバックアップをクリーンアップ
                self._cleanup_old_backups()
                
                return backup_info
                
            except Exception as e:
                self.logger.error(f"Failed to create backup: {e}")
                raise
    
    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None) -> str:
        """
        バックアップを復元
        
        Args:
            backup_id: バックアップID
            restore_path: 復元先パス（Noneの場合は元の場所）
        
        Returns:
            str: 復元先パス
        """
        backup_info = self._get_backup_info(backup_id)
        
        if backup_info is None:
            raise ValueError(f"Backup not found: {backup_id}")
        
        backup_path = Path(backup_info.backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # 復元先を決定
        if restore_path is None:
            restore_path = backup_info.source_path
        
        restore_dest = Path(restore_path)
        
        with self._backup_lock:
            try:
                # 既存ファイルがあれば一時バックアップ
                temp_backup = None
                if restore_dest.exists():
                    temp_backup = restore_dest.with_suffix(restore_dest.suffix + '.tmp')
                    if restore_dest.is_file():
                        shutil.move(restore_dest, temp_backup)
                    else:
                        shutil.move(restore_dest, temp_backup)
                
                # バックアップを復元
                if backup_path.is_file():
                    shutil.copy2(backup_path, restore_dest)
                else:
                    shutil.copytree(backup_path, restore_dest)
                
                # チェックサムを検証
                restored_checksum = self._calculate_checksum(restore_dest)
                if restored_checksum != backup_info.checksum:
                    # チェックサム不一致の場合は元に戻す
                    if temp_backup and temp_backup.exists():
                        restore_dest.unlink() if restore_dest.is_file() else shutil.rmtree(restore_dest)
                        shutil.move(temp_backup, restore_dest)
                    raise ValueError("Checksum mismatch after restore")
                
                # 一時バックアップを削除
                if temp_backup and temp_backup.exists():
                    temp_backup.unlink() if temp_backup.is_file() else shutil.rmtree(temp_backup)
                
                self.logger.info(f"Backup restored: {backup_id} to {restore_path}")
                
                return str(restore_dest)
                
            except Exception as e:
                self.logger.error(f"Failed to restore backup {backup_id}: {e}")
                raise
    
    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """バックアップ情報を取得"""
        for backup in self.backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def _generate_backup_id(self) -> str:
        """バックアップIDを生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"backup_{timestamp}"
    
    def _calculate_checksum(self, path: Path) -> str:
        """ファイルまたはディレクトリのチェックサムを計算"""
        if path.is_file():
            return self._calculate_file_checksum(path)
        else:
            # ディレクトリの場合は全ファイルのチェックサムを結合
            checksums = []
            for file_path in sorted(path.rglob('*')):
                if file_path.is_file():
                    checksums.append(self._calculate_file_checksum(file_path))
            combined = ''.join(checksums)
            return hashlib.sha256(combined.encode()).hexdigest()
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """ファイルのチェックサムを計算"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_size(self, path: Path) -> int:
        """ファイルまたはディレクトリのサイズを取得"""
        if path.is_file():
            return path.stat().st_size
        else:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
    
    def _save_backup_index(self):
        """バックアップインデックスを保存"""
        index_file = self.backup_dir / 'backup_index.json'
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [backup.to_dict() for backup in self.backups],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            self.logger.error(f"Failed to save backup index: {e}")
    
    def _load_backup_index(self):
        """バックアップインデックスを読み込み"""
        index_file = self.backup_dir / 'backup_index.json'
        if not index_file.exists():
            return
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.backups = [
                BackupInfo(**item) for item in data
            ]
        except Exception as e:
            self.logger.error(f"Failed to load backup index: {e}")
    
    def _cleanup_old_backups(self):
        """古いバックアップをクリーンアップ"""
        if len(self.backups) <= self.max_backups:
            return
        
        # タイムスタンプでソート
        self.backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 古いものを削除
        for backup in self.backups[self.max_backups:]:
            backup_path = Path(backup.backup_path)
            try:
                if backup_path.exists():
                    if backup_path.is_file():
                        backup_path.unlink()
                    else:
                        shutil.rmtree(backup_path)
                self.logger.debug(f"Deleted old backup: {backup.backup_id}")
            except Exception as e:
                self.logger.warning(f"Failed to delete backup {backup.backup_id}: {e}")
        
        # リストを更新
        self.backups = self.backups[:self.max_backups]
        self._save_backup_index()
    
    # ========================================================================
    # 自動バックアップ機能 (Auto Backup Functions)
    # ========================================================================
    
    def start_auto_backup(self, source_paths: List[str]):
        """
        自動バックアップを開始
        
        Args:
            source_paths: バックアップ対象のパスリスト
        """
        if self.auto_backup_enabled:
            self.logger.warning("Auto backup is already running")
            return
        
        self.auto_backup_enabled = True
        self.auto_backup_thread = threading.Thread(
            target=self._auto_backup_worker,
            args=(source_paths,),
            daemon=True
        )
        self.auto_backup_thread.start()
        
        self.logger.info(
            f"Auto backup started (interval: {self.auto_backup_interval}s, "
            f"paths: {len(source_paths)})"
        )
    
    def stop_auto_backup(self):
        """自動バックアップを停止"""
        if not self.auto_backup_enabled:
            return
        
        self.auto_backup_enabled = False
        
        if self.auto_backup_thread:
            self.auto_backup_thread.join(timeout=5)
        
        self.logger.info("Auto backup stopped")
    
    def _auto_backup_worker(self, source_paths: List[str]):
        """自動バックアップワーカー"""
        while self.auto_backup_enabled:
            try:
                for source_path in source_paths:
                    if not self.auto_backup_enabled:
                        break
                    
                    source = Path(source_path)
                    if source.exists():
                        self.create_backup(source_path)
                
            except Exception as e:
                self.logger.error(f"Error in auto backup worker: {e}")
            
            # 次のバックアップまで待機
            time.sleep(self.auto_backup_interval)
    
    # ========================================================================
    # クラッシュ復旧機能 (Crash Recovery Functions)
    # ========================================================================
    
    def _check_crash_recovery(self):
        """クラッシュ復旧をチェック"""
        self.logger.info("Checking for crash recovery...")
        
        # 実行中または一時停止中のチェックポイントを検索
        recoverable_operations = []
        
        for checkpoint_file in self.checkpoint_dir.glob('*.json'):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                state = ProcessState(data['state'])
                if state in [ProcessState.RUNNING, ProcessState.PAUSED]:
                    recoverable_operations.append(data)
            except Exception as e:
                self.logger.warning(f"Failed to check checkpoint {checkpoint_file}: {e}")
        
        if recoverable_operations:
            self.logger.warning(
                f"Found {len(recoverable_operations)} operations that may need recovery"
            )
            for op in recoverable_operations:
                self.logger.info(
                    f"  - {op['operation_name']} (ID: {op['operation_id']}, "
                    f"progress: {op['progress']:.1%})"
                )
        else:
            self.logger.info("No operations need recovery")
    
    def get_recoverable_operations(self) -> List[Dict[str, Any]]:
        """
        復旧可能な操作のリストを取得
        
        Returns:
            List[Dict[str, Any]]: 復旧可能な操作のリスト
        """
        recoverable = []
        
        for checkpoint_file in self.checkpoint_dir.glob('*.json'):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                state = ProcessState(data['state'])
                if state in [ProcessState.RUNNING, ProcessState.PAUSED]:
                    recoverable.append(data)
            except Exception as e:
                self.logger.warning(f"Failed to check checkpoint {checkpoint_file}: {e}")
        
        return recoverable
    
    # ========================================================================
    # 統計・管理機能 (Statistics and Management Functions)
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            'checkpoints': {
                'total': len(self.checkpoints),
                'by_state': self._count_by_state(),
                'active_operations': len(self.active_operations)
            },
            'backups': {
                'total': len(self.backups),
                'total_size_mb': sum(b.size_bytes for b in self.backups) / (1024 * 1024),
                'oldest': self.backups[0].timestamp if self.backups else None,
                'newest': self.backups[-1].timestamp if self.backups else None
            },
            'auto_backup': {
                'enabled': self.auto_backup_enabled,
                'interval_seconds': self.auto_backup_interval
            }
        }
    
    def _count_by_state(self) -> Dict[str, int]:
        """状態別のチェックポイント数をカウント"""
        counts = {}
        for checkpoint in self.checkpoints.values():
            state = checkpoint.state.value
            counts[state] = counts.get(state, 0) + 1
        return counts
    
    def clear_completed_checkpoints(self):
        """完了したチェックポイントをクリア"""
        completed_ids = [
            cp_id for cp_id, cp in self.checkpoints.items()
            if cp.state == ProcessState.COMPLETED
        ]
        
        for cp_id in completed_ids:
            checkpoint_file = self.checkpoint_dir / f"{cp_id}.json"
            try:
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
                del self.checkpoints[cp_id]
            except Exception as e:
                self.logger.warning(f"Failed to delete checkpoint {cp_id}: {e}")
        
        self.logger.info(f"Cleared {len(completed_ids)} completed checkpoints")


# ================================================================================
# グローバルフェイルセーフマネージャーインスタンス
# ================================================================================

_global_failsafe_manager: Optional[FailsafeManager] = None


def get_failsafe_manager() -> FailsafeManager:
    """グローバルフェイルセーフマネージャーを取得"""
    global _global_failsafe_manager
    if _global_failsafe_manager is None:
        _global_failsafe_manager = FailsafeManager()
    return _global_failsafe_manager
