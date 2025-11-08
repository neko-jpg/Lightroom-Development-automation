"""
Database initialization script for Junmai AutoDev.
Creates the database schema and optionally seeds initial data.
"""

import pathlib
import sys
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from models.database import (
    init_db,
    get_session,
    Session,
    Photo,
    Job,
    Preset,
    Statistic,
    LearningData
)


def create_database(database_url: str = None, echo: bool = False):
    """
    Create the database and all tables.
    
    Args:
        database_url: SQLAlchemy database URL (default: sqlite:///data/junmai.db)
        echo: Whether to echo SQL statements
    """
    if database_url is None:
        # Ensure data directory exists
        data_dir = pathlib.Path(__file__).parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        database_url = f'sqlite:///{data_dir}/junmai.db'
    
    print(f"Initializing database at: {database_url}")
    
    try:
        engine = init_db(database_url, echo=echo)
        print("✓ Database schema created successfully")
        print(f"✓ Tables created: sessions, photos, jobs, presets, statistics, learning_data")
        return engine
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        raise


def seed_initial_data():
    """
    Seed the database with initial preset data.
    """
    print("\nSeeding initial data...")
    
    db = get_session()
    
    try:
        # Check if presets already exist
        existing_presets = db.query(Preset).count()
        if existing_presets > 0:
            print(f"  Database already contains {existing_presets} presets. Skipping seed.")
            return
        
        # Create default presets
        default_presets = [
            {
                'name': 'WhiteLayer_Transparency_v4',
                'version': 'v4',
                'context_tags': ['backlit_portrait', 'soft_light', 'portrait'],
                'config_template': {
                    'version': '1.0',
                    'pipeline': [
                        {
                            'stage': 'base',
                            'settings': {
                                'Exposure2012': -0.15,
                                'Highlights2012': -18,
                                'Shadows2012': 12
                            }
                        },
                        {
                            'stage': 'HSL',
                            'hue': {'orange': -4},
                            'sat': {'orange': -6, 'blue': -8},
                            'lum': {'orange': 4, 'blue': -6}
                        }
                    ],
                    'safety': {
                        'snapshot': True,
                        'dryRun': False
                    }
                },
                'blend_amount': 60,
                'usage_count': 0,
                'avg_approval_rate': None
            },
            {
                'name': 'LowLight_NR_v2',
                'version': 'v2',
                'context_tags': ['low_light_indoor', 'night', 'high_iso'],
                'config_template': {
                    'version': '1.0',
                    'pipeline': [
                        {
                            'stage': 'base',
                            'settings': {
                                'Exposure2012': 0.3,
                                'Shadows2012': 25,
                                'Blacks2012': -10
                            }
                        },
                        {
                            'stage': 'detail',
                            'nr': {
                                'luminance': 40,
                                'color': 30
                            }
                        }
                    ],
                    'safety': {
                        'snapshot': True,
                        'dryRun': False
                    }
                },
                'blend_amount': 80,
                'usage_count': 0,
                'avg_approval_rate': None
            },
            {
                'name': 'Landscape_Sky_v3',
                'version': 'v3',
                'context_tags': ['landscape_sky', 'outdoor', 'landscape'],
                'config_template': {
                    'version': '1.0',
                    'pipeline': [
                        {
                            'stage': 'base',
                            'settings': {
                                'Exposure2012': 0.0,
                                'Highlights2012': -30,
                                'Shadows2012': 15,
                                'Clarity2012': 10
                            }
                        },
                        {
                            'stage': 'HSL',
                            'sat': {'blue': 10, 'aqua': 15},
                            'lum': {'blue': -5}
                        }
                    ],
                    'safety': {
                        'snapshot': True,
                        'dryRun': False
                    }
                },
                'blend_amount': 70,
                'usage_count': 0,
                'avg_approval_rate': None
            }
        ]
        
        for preset_data in default_presets:
            preset = Preset(
                name=preset_data['name'],
                version=preset_data['version'],
                blend_amount=preset_data['blend_amount'],
                usage_count=preset_data['usage_count'],
                avg_approval_rate=preset_data['avg_approval_rate']
            )
            preset.set_context_tags(preset_data['context_tags'])
            preset.set_config_template(preset_data['config_template'])
            db.add(preset)
        
        db.commit()
        print(f"✓ Seeded {len(default_presets)} default presets")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
        raise
    finally:
        db.close()


def verify_database():
    """
    Verify the database was created correctly.
    """
    print("\nVerifying database...")
    
    db = get_session()
    
    try:
        # Check each table
        tables = {
            'sessions': Session,
            'photos': Photo,
            'jobs': Job,
            'presets': Preset,
            'statistics': Statistic,
            'learning_data': LearningData
        }
        
        for table_name, model in tables.items():
            count = db.query(model).count()
            print(f"  ✓ Table '{table_name}': {count} records")
        
        print("\n✓ Database verification complete")
        
    except Exception as e:
        print(f"✗ Error verifying database: {e}")
        raise
    finally:
        db.close()


def main():
    """Main entry point for database initialization"""
    parser = argparse.ArgumentParser(
        description='Initialize Junmai AutoDev database'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='SQLAlchemy database URL (default: sqlite:///data/junmai.db)'
    )
    parser.add_argument(
        '--echo',
        action='store_true',
        help='Echo SQL statements (for debugging)'
    )
    parser.add_argument(
        '--no-seed',
        action='store_true',
        help='Skip seeding initial data'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing database'
    )
    
    args = parser.parse_args()
    
    try:
        if not args.verify_only:
            # Create database
            create_database(args.database_url, args.echo)
            
            # Seed initial data
            if not args.no_seed:
                seed_initial_data()
        
        # Verify database
        verify_database()
        
        print("\n" + "="*50)
        print("Database initialization complete!")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
