from app import db
from app import app

ROLE_USER = 0
ROLE_LANDLORD = 1
ROLE_ADMIN = 2

TYPE_ELECTRICITY = 0
TYPE_HEAT = 1
TYPE_WATER = 2
TYPE_ELECTRICITY_INST = 3

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    rooms = db.relationship('Room',secondary='contract', lazy='dynamic')
    facebook_id = db.Column(db.String(64))

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname = nickname).first() == None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname = new_nickname).first() == None:
                break
            version += 1
        return new_nickname
        
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
        
    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Property(db.Model):
    __tablename__ = 'property'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(140), unique = True)
    users = db.relationship('User', backref = 'property', lazy = 'dynamic')
    info = db.Column(db.String(140))
    prices = db.relationship('Prices', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")
    rooms = db.relationship('Room', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")
    feeds = db.relationship('Feed', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")

    def get_current_prices(self):
        return Prices.query.join(Property, (Property.id == Prices.property_id)).filter(Property.id == self.id).order_by(Prices.start_date.desc()).first()

    def get_prices(self):
        return Prices.query.filter(Prices.property_id == self.id).order_by(Prices.start_date.desc())

    def get_contracts(self):
        return Contract.query.join(Room).filter(Room.property_id == self.id)

    def get_all_datastreams(self):
        return Datastream.query.join(Feed).filter(Feed.property_id == self.id)

    def __repr__(self):
        return '<Property %r>' % (self.name)

class Prices(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, primary_key = True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    electricity = db.Column(db.Integer, default = 0) # IN CENTS!
    heat = db.Column(db.Integer, default = 0)
    water = db.Column(db.Integer, default = 0)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key = True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    name = db.Column(db.String(140))
    info = db.Column(db.String(140))
    users = db.relationship('User', secondary='contract', lazy='dynamic')
    datastreams = db.relationship('Datastream', secondary='room_datastream', lazy='dynamic')

    def get_connection(self,datastream_id):
        return Room_Datastream.query.filter(Room_Datastream.room_id==self.id,Room_Datastream.datastream_id==datastream_id).first()

class Feed(db.Model):
    __tablename__ = 'feed'
    id = db.Column(db.Integer, primary_key = True)
    xively_id = db.Column(db.Integer)
    api_key = db.Column(db.String(140))
    info = db.Column(db.String(140))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    datastreams = db.relationship('Datastream', backref = 'feed', lazy = 'dynamic', cascade="all, delete, delete-orphan")

    def get_type(self,dataType):
        d = Datastream.query.filter(Datastream.feed_id == self.id,Datastream.type == dataType)
        if d == None:
            return None
        else:
            return d

class Datastream(db.Model):
    __tablename__ = 'datastream'
    id = db.Column(db.Integer, primary_key = True)
    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'))
    xively_id = db.Column(db.String(140))
    unit = db.Column(db.String(64))
    info = db.Column(db.String(140), default='No info')
    type = db.Column(db.SmallInteger)
    rooms = db.relationship('Room', secondary='room_datastream', lazy='dynamic')

    def get_connection(self,room_id):
        return Room_Datastream.query.filter(Room_Datastream.datastream_id==self.id,Room_Datastream.room_id==room_id).first()
        
class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    user = db.relationship('User', backref="room_assoc")
    room = db.relationship('Room', backref="user_assoc")

class Room_Datastream(db.Model):
    __tablename__ = 'room_datastream'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    datastream_id = db.Column(db.Integer, db.ForeignKey('datastream.id'))
    room = db.relationship('Room', backref="datastream_assoc")
    datastream = db.relationship('Datastream', backref="room_assoc")