"""Add A/B testing tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create A/B testing tables"""
    
    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preset_a_id', sa.Integer(), nullable=False),
        sa.Column('preset_b_id', sa.Integer(), nullable=False),
        sa.Column('context_tag', sa.String(100), nullable=True),
        sa.Column('target_sample_size', sa.Integer(), nullable=True, default=100),
        sa.Column('duration_days', sa.Integer(), nullable=True, default=30),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'paused', 'completed')", name='ck_ab_tests_status'),
        sa.ForeignKeyConstraint(['preset_a_id'], ['presets.id'], ),
        sa.ForeignKeyConstraint(['preset_b_id'], ['presets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ab_test_assignments table
    op.create_table(
        'ab_test_assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('variant', sa.String(1), nullable=False),
        sa.Column('preset_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('result_recorded_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("variant IN ('A', 'B')", name='ck_ab_test_assignments_variant'),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ),
        sa.ForeignKeyConstraint(['preset_id'], ['presets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_ab_tests_status', 'ab_tests', ['status'])
    op.create_index('idx_ab_test_assignments_test', 'ab_test_assignments', ['test_id'])
    op.create_index('idx_ab_test_assignments_photo', 'ab_test_assignments', ['photo_id'])
    op.create_index('idx_ab_test_assignments_variant', 'ab_test_assignments', ['variant'])


def downgrade():
    """Drop A/B testing tables"""
    
    # Drop indexes
    op.drop_index('idx_ab_test_assignments_variant', table_name='ab_test_assignments')
    op.drop_index('idx_ab_test_assignments_photo', table_name='ab_test_assignments')
    op.drop_index('idx_ab_test_assignments_test', table_name='ab_test_assignments')
    op.drop_index('idx_ab_tests_status', table_name='ab_tests')
    
    # Drop tables
    op.drop_table('ab_test_assignments')
    op.drop_table('ab_tests')
