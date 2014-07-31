from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
price = Table('price', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('property_id', INTEGER),
    Column('electricity', INTEGER),
    Column('heat', INTEGER),
    Column('water', INTEGER),
    Column('start_date', DATETIME),
    Column('end_date', DATETIME),
)

prices = Table('prices', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('property_id', Integer),
    Column('electricity', Integer, default=ColumnDefault(0)),
    Column('heat', Integer, default=ColumnDefault(0)),
    Column('water', Integer, default=ColumnDefault(0)),
    Column('start_date', DateTime),
    Column('end_date', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['price'].drop()
    post_meta.tables['prices'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['price'].create()
    post_meta.tables['prices'].drop()
