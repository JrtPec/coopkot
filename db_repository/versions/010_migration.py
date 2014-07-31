from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
price = Table('price', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('property_id', Integer),
    Column('electricity', Numeric, default=ColumnDefault(0)),
    Column('heat', Numeric, default=ColumnDefault(0)),
    Column('water', Numeric, default=ColumnDefault(0)),
    Column('start_date', Date),
    Column('end_date', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['price'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['price'].drop()
