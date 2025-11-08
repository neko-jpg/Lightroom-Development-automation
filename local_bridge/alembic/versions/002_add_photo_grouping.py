"""Add photo grouping support

Revision ID: 002
Revises: 001
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add photo grouping tables and fields."""
    
    # Create photo_groups table
    op.create_table(
        'photo_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('similarity_threshold', sa.Integer(), nullable=False),
        sa.Column('avg_similarity', sa.Float(), nullable=True),
        sa.Column('photo_count', sa.Integer(), nullable=True),
        sa.Column('best_photo_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add new columns to photos table
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phash', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('photo_group_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_best_in_group', sa.Boolean(), nullable=True))
        batch_op.create_foreign_key('fk_photos_photo_group_id', 'photo_groups', ['photo_group_id'], ['id'])
    
    # Create indexes
    op.create_index('idx_photos_group', 'photos', ['photo_group_id'], unique=False)
    op.create_index('idx_photos_phash', 'photos', ['phash'], unique=False)
    op.create_index('idx_photo_groups_session', 'photo_groups', ['session_id'], unique=False)


def downgrade():
    """Remove photo grouping tables and fields."""
    
    # Drop indexes
    op.drop_index('idx_photo_groups_session', table_name='photo_groups')
    op.drop_index('idx_photos_phash', table_name='photos')
    op.drop_index('idx_photos_group', table_name='photos')
    
    # Remove columns from photos table
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_photos_photo_group_id', type_='foreignkey')
        batch_op.drop_column('is_best_in_group')
        batch_op.drop_column('photo_group_id')
        batch_op.drop_column('phash')
    
    # Drop photo_groups table
    op.drop_table('photo_groups')
