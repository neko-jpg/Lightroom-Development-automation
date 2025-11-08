"""
Database models for Junmai AutoDev system.
Implements SQLAlchemy models for sessions, photos, jobs, presets, statistics, and learning data.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
    Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool
import json

Base = declarative_base()


class Session(Base):
    """セッション管理テーブル"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    import_folder = Column(String(512))
    total_photos = Column(Integer, default=0)
    processed_photos = Column(Integer, default=0)
    status = Column(
        String(50),
        CheckConstraint("status IN ('importing', 'selecting', 'developing', 'exporting', 'completed')"),
        nullable=False,
        default='importing'
    )
    
    # Relationships
    photos = relationship('Photo', back_populates='session', cascade='all, delete-orphan')
    statistics = relationship('Statistic', back_populates='session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Session(id={self.id}, name='{self.name}', status='{self.status}')>"


class Photo(Base):
    """写真メタデータテーブル"""
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=True)
    file_path = Column(String(1024), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    import_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # EXIF データ
    camera_make = Column(String(100))
    camera_model = Column(String(100))
    lens = Column(String(100))
    focal_length = Column(Float)
    aperture = Column(Float)
    shutter_speed = Column(String(50))
    iso = Column(Integer)
    capture_time = Column(DateTime)
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    
    # AI評価
    ai_score = Column(Float, CheckConstraint('ai_score >= 1 AND ai_score <= 5'))
    focus_score = Column(Float)
    exposure_score = Column(Float)
    composition_score = Column(Float)
    subject_type = Column(String(100))
    detected_faces = Column(Integer, default=0)
    
    # コンテキスト
    context_tag = Column(String(100))
    selected_preset = Column(String(100))
    
    # 類似写真グループ化
    phash = Column(String(64))  # Perceptual hash for similarity detection
    photo_group_id = Column(Integer, ForeignKey('photo_groups.id'), nullable=True)
    is_best_in_group = Column(Boolean, default=False)
    
    # 処理状態
    status = Column(
        String(50),
        CheckConstraint("status IN ('imported', 'analyzed', 'queued', 'processing', 'completed', 'failed', 'rejected')"),
        nullable=False,
        default='imported'
    )
    lr_catalog_id = Column(String(100))
    virtual_copy_id = Column(String(100))
    
    # 承認
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Relationships
    session = relationship('Session', back_populates='photos')
    jobs = relationship('Job', back_populates='photo', cascade='all, delete-orphan')
    learning_data = relationship('LearningData', back_populates='photo', cascade='all, delete-orphan')
    photo_group = relationship('PhotoGroup', back_populates='photos')
    
    def __repr__(self):
        return f"<Photo(id={self.id}, file_name='{self.file_name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert photo to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'import_time': self.import_time.isoformat() if self.import_time else None,
            'camera_make': self.camera_make,
            'camera_model': self.camera_model,
            'lens': self.lens,
            'focal_length': self.focal_length,
            'aperture': self.aperture,
            'shutter_speed': self.shutter_speed,
            'iso': self.iso,
            'capture_time': self.capture_time.isoformat() if self.capture_time else None,
            'ai_score': self.ai_score,
            'focus_score': self.focus_score,
            'exposure_score': self.exposure_score,
            'composition_score': self.composition_score,
            'subject_type': self.subject_type,
            'detected_faces': self.detected_faces,
            'context_tag': self.context_tag,
            'selected_preset': self.selected_preset,
            'status': self.status,
            'approved': self.approved,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


class Job(Base):
    """ジョブキューテーブル"""
    __tablename__ = 'jobs'
    
    id = Column(String(100), primary_key=True)
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=True)
    priority = Column(Integer, CheckConstraint('priority IN (1, 2, 3)'), nullable=False, default=2)
    config_json = Column(Text, nullable=False)
    status = Column(
        String(50),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')"),
        nullable=False,
        default='pending'
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    photo = relationship('Photo', back_populates='jobs')
    
    def __repr__(self):
        return f"<Job(id='{self.id}', status='{self.status}', priority={self.priority})>"
    
    def get_config(self):
        """Parse and return config JSON"""
        return json.loads(self.config_json) if self.config_json else {}
    
    def set_config(self, config_dict):
        """Set config from dictionary"""
        self.config_json = json.dumps(config_dict, ensure_ascii=False)


class Preset(Base):
    """プリセット管理テーブル"""
    __tablename__ = 'presets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    version = Column(String(50), nullable=False)
    context_tags = Column(Text)  # JSON array
    config_template = Column(Text, nullable=False)  # JSON
    blend_amount = Column(Integer, default=100)
    usage_count = Column(Integer, default=0)
    avg_approval_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Preset(id={self.id}, name='{self.name}', version='{self.version}')>"
    
    def get_context_tags(self):
        """Parse and return context tags"""
        return json.loads(self.context_tags) if self.context_tags else []
    
    def set_context_tags(self, tags_list):
        """Set context tags from list"""
        self.context_tags = json.dumps(tags_list, ensure_ascii=False)
    
    def get_config_template(self):
        """Parse and return config template"""
        return json.loads(self.config_template) if self.config_template else {}
    
    def set_config_template(self, config_dict):
        """Set config template from dictionary"""
        self.config_template = json.dumps(config_dict, ensure_ascii=False)


class Statistic(Base):
    """統計データテーブル"""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=True)
    total_imported = Column(Integer, default=0)
    total_selected = Column(Integer, default=0)
    total_processed = Column(Integer, default=0)
    total_exported = Column(Integer, default=0)
    avg_processing_time = Column(Float)
    success_rate = Column(Float)
    preset_usage = Column(Text)  # JSON object
    
    # Relationships
    session = relationship('Session', back_populates='statistics')
    
    def __repr__(self):
        return f"<Statistic(id={self.id}, date='{self.date}', session_id={self.session_id})>"
    
    def get_preset_usage(self):
        """Parse and return preset usage"""
        return json.loads(self.preset_usage) if self.preset_usage else {}
    
    def set_preset_usage(self, usage_dict):
        """Set preset usage from dictionary"""
        self.preset_usage = json.dumps(usage_dict, ensure_ascii=False)


class LearningData(Base):
    """ユーザー学習データテーブル"""
    __tablename__ = 'learning_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=False)
    action = Column(
        String(50),
        CheckConstraint("action IN ('approved', 'rejected', 'modified')"),
        nullable=False
    )
    original_preset = Column(String(255))
    final_preset = Column(String(255))
    parameter_adjustments = Column(Text)  # JSON
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    photo = relationship('Photo', back_populates='learning_data')
    
    def __repr__(self):
        return f"<LearningData(id={self.id}, photo_id={self.photo_id}, action='{self.action}')>"
    
    def get_parameter_adjustments(self):
        """Parse and return parameter adjustments"""
        return json.loads(self.parameter_adjustments) if self.parameter_adjustments else {}
    
    def set_parameter_adjustments(self, adjustments_dict):
        """Set parameter adjustments from dictionary"""
        self.parameter_adjustments = json.dumps(adjustments_dict, ensure_ascii=False)


class PhotoGroup(Base):
    """写真グループテーブル（類似写真のグループ化）"""
    __tablename__ = 'photo_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    similarity_threshold = Column(Integer, nullable=False)
    avg_similarity = Column(Float)
    photo_count = Column(Integer, default=0)
    best_photo_id = Column(Integer)
    
    # Relationships
    photos = relationship('Photo', back_populates='photo_group')
    
    def __repr__(self):
        return f"<PhotoGroup(id={self.id}, photo_count={self.photo_count}, best_photo_id={self.best_photo_id})>"
    
    def to_dict(self):
        """Convert photo group to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'similarity_threshold': self.similarity_threshold,
            'avg_similarity': self.avg_similarity,
            'photo_count': self.photo_count,
            'best_photo_id': self.best_photo_id
        }


class ABTest(Base):
    """A/Bテストテーブル"""
    __tablename__ = 'ab_tests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    preset_a_id = Column(Integer, ForeignKey('presets.id'), nullable=False)
    preset_b_id = Column(Integer, ForeignKey('presets.id'), nullable=False)
    context_tag = Column(String(100))
    target_sample_size = Column(Integer, default=100)
    duration_days = Column(Integer, default=30)
    status = Column(
        String(50),
        CheckConstraint("status IN ('active', 'paused', 'completed')"),
        nullable=False,
        default='active'
    )
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    preset_a = relationship('Preset', foreign_keys=[preset_a_id])
    preset_b = relationship('Preset', foreign_keys=[preset_b_id])
    assignments = relationship('ABTestAssignment', back_populates='ab_test', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ABTest(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert A/B test to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'preset_a_id': self.preset_a_id,
            'preset_b_id': self.preset_b_id,
            'context_tag': self.context_tag,
            'target_sample_size': self.target_sample_size,
            'duration_days': self.duration_days,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ABTestAssignment(Base):
    """A/Bテスト割り当てテーブル"""
    __tablename__ = 'ab_test_assignments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey('ab_tests.id'), nullable=False)
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=False)
    variant = Column(
        String(1),
        CheckConstraint("variant IN ('A', 'B')"),
        nullable=False
    )
    preset_id = Column(Integer, ForeignKey('presets.id'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved = Column(Boolean)
    processing_time = Column(Float)
    result_recorded_at = Column(DateTime)
    
    # Relationships
    ab_test = relationship('ABTest', back_populates='assignments')
    photo = relationship('Photo')
    preset = relationship('Preset')
    
    def __repr__(self):
        return f"<ABTestAssignment(id={self.id}, test_id={self.test_id}, variant='{self.variant}')>"
    
    def to_dict(self):
        """Convert assignment to dictionary for API responses"""
        return {
            'id': self.id,
            'test_id': self.test_id,
            'photo_id': self.photo_id,
            'variant': self.variant,
            'preset_id': self.preset_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'approved': self.approved,
            'processing_time': self.processing_time,
            'result_recorded_at': self.result_recorded_at.isoformat() if self.result_recorded_at else None
        }


# Create indexes for performance
Index('idx_photos_session', Photo.session_id)
Index('idx_photos_status', Photo.status)
Index('idx_photos_group', Photo.photo_group_id)
Index('idx_photos_phash', Photo.phash)
Index('idx_jobs_status', Job.status)
Index('idx_jobs_priority', Job.priority)
Index('idx_statistics_date', Statistic.date)
Index('idx_photo_groups_session', PhotoGroup.session_id)
Index('idx_ab_tests_status', ABTest.status)
Index('idx_ab_test_assignments_test', ABTestAssignment.test_id)
Index('idx_ab_test_assignments_photo', ABTestAssignment.photo_id)
Index('idx_ab_test_assignments_variant', ABTestAssignment.variant)


# Database initialization and session management
_engine = None
_SessionLocal = None


def init_db(database_url: str = 'sqlite:///data/junmai.db', echo: bool = False):
    """
    Initialize the database engine and create all tables.
    
    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements (for debugging)
    """
    global _engine, _SessionLocal
    
    # For SQLite, use StaticPool to avoid threading issues
    if database_url.startswith('sqlite'):
        _engine = create_engine(
            database_url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=echo
        )
    else:
        _engine = create_engine(database_url, echo=echo)
    
    # Create all tables
    Base.metadata.create_all(bind=_engine)
    
    # Create session factory
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    return _engine


def get_session():
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy session object
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return _SessionLocal()


def get_engine():
    """Get the database engine"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine
