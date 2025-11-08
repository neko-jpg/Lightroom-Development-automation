"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-11-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('import_folder', sa.String(length=512), nullable=True),
        sa.Column('total_photos', sa.Integer(), nullable=True),
        sa.Column('processed_photos', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.CheckConstraint("status IN ('importing', 'selecting', 'developing', 'exporting', 'completed')"),
        sa.PrimaryKeyConstraint('id')
    )

    # Create photos table
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('import_time', sa.DateTime(), nullable=False),
        sa.Column('camera_make', sa.String(length=100), nullable=True),
        sa.Column('camera_model', sa.String(length=100), nullable=True),
        sa.Column('lens', sa.String(length=100), nullable=True),
        sa.Column('focal_length', sa.Float(), nullable=True),
        sa.Column('aperture', sa.Float(), nullable=True),
        sa.Column('shutter_speed', sa.String(length=50), nullable=True),
        sa.Column('iso', sa.Integer(), nullable=True),
        sa.Column('capture_time', sa.DateTime(), nullable=True),
        sa.Column('gps_lat', sa.Float(), nullable=True),
        sa.Column('gps_lon', sa.Float(), nullable=True),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('focus_score', sa.Float(), nullable=True),
        sa.Column('exposure_score', sa.Float(), nullable=True),
        sa.Column('composition_score', sa.Float(), nullable=True),
        sa.Column('subject_type', sa.String(length=100), nullable=True),
        sa.Column('detected_faces', sa.Integer(), nullable=True),
        sa.Column('context_tag', sa.String(length=100), nullable=True),
        sa.Column('selected_preset', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('lr_catalog_id', sa.String(length=100), nullable=True),
        sa.Column('virtual_copy_id', sa.String(length=100), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.CheckConstraint('ai_score >= 1 AND ai_score <= 5'),
        sa.CheckConstraint("status IN ('imported', 'analyzed', 'queued', 'processing', 'completed', 'failed', 'rejected')"),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )
    op.create_index('idx_photos_session', 'photos', ['session_id'])
    op.create_index('idx_photos_status', 'photos', ['status'])

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('config_json', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.CheckConstraint('priority IN (1, 2, 3)'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')"),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_priority', 'jobs', ['priority'])

    # Create presets table
    op.create_table(
        'presets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('context_tags', sa.Text(), nullable=True),
        sa.Column('config_template', sa.Text(), nullable=False),
        sa.Column('blend_amount', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('avg_approval_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create statistics table
    op.create_table(
        'statistics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('total_imported', sa.Integer(), nullable=True),
        sa.Column('total_selected', sa.Integer(), nullable=True),
        sa.Column('total_processed', sa.Integer(), nullable=True),
        sa.Column('total_exported', sa.Integer(), nullable=True),
        sa.Column('avg_processing_time', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('preset_usage', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_statistics_date', 'statistics', ['date'])

    # Create learning_data table
    op.create_table(
        'learning_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('original_preset', sa.String(length=255), nullable=True),
        sa.Column('final_preset', sa.String(length=255), nullable=True),
        sa.Column('parameter_adjustments', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.CheckConstraint("action IN ('approved', 'rejected', 'modified')"),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('learning_data')
    op.drop_index('idx_statistics_date', table_name='statistics')
    op.drop_table('statistics')
    op.drop_table('presets')
    op.drop_index('idx_jobs_priority', table_name='jobs')
    op.drop_index('idx_jobs_status', table_name='jobs')
    op.drop_table('jobs')
    op.drop_index('idx_photos_status', table_name='photos')
    op.drop_index('idx_photos_session', table_name='photos')
    op.drop_table('photos')
    op.drop_table('sessions')
