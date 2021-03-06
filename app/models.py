from app import db
from app import app
from datetime import date, datetime

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
    phone = db.Column(db.String(140), default='')
    phone_2 = db.Column(db.String(140), default='')
    bank_IBAN = db.Column(db.String(140), default='')
    bank_BIC = db.Column(db.String(140), default='')
    street = db.Column(db.String(140), default='')
    number = db.Column(db.String(140), default='')
    postcode = db.Column(db.String(140), default='')
    city = db.Column(db.String(140), default='')
    country = db.Column(db.String(140), default='')
    feedback_messages = db.relationship('Feedback', backref = 'sender', lazy = 'dynamic')

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

    def is_admin(self):
        if self.role == ROLE_ADMIN:
            return True
        else:
            return False

    def is_landlord(self):
        if self.role > ROLE_LANDLORD:
            return True
        else:
            return False

    def is_excl_landlord(self):
        if self.role == ROLE_LANDLORD:
            return True
        else:
            return False

    def get_id(self):
        return unicode(self.id)

    def get_datastream_type(self,dataType):
        c = Contract.query.filter(self == Contract.user).order_by(Contract.start_date.desc()).first()
        if c == None:
            return None
        if c.is_current():
            return c.room.datastreams.filter(Datastream.type == dataType).order_by(Datastream.info)
        else:
            return None

    def get_room(self):
        c = Contract.query.filter(self==Contract.user).order_by(Contract.start_date.desc()).first()
        if c == None:
            return None
        if c.is_current():

            return int(c.room_id)
        else:
            return None

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Property(db.Model):
    __tablename__ = 'property'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(140), unique = True)
    users = db.relationship('User', backref = 'property', lazy = 'dynamic')
    prices = db.relationship('Prices', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")
    rooms = db.relationship('Room', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")
    feeds = db.relationship('Feed', backref = 'property', lazy = 'dynamic', cascade="all, delete, delete-orphan")
    street = db.Column(db.String(140), default='')
    number = db.Column(db.String(140), default='')
    postcode = db.Column(db.String(140), default='')
    city = db.Column(db.String(140), default='')
    country = db.Column(db.String(140), default='')
    bank_IBAN = db.Column(db.String(140), default='')
    bank_BIC = db.Column(db.String(140), default='')
    vat_nr = db.Column(db.String(140), default='')
    contact_name = db.Column(db.String(140), default='')
    contact_mail = db.Column(db.String(140), default='')
    contact_phone = db.Column(db.String(140), default='')  
    billing_street = db.Column(db.String(140), default='')
    billing_number = db.Column(db.String(140), default='')
    billing_postcode = db.Column(db.String(140), default='')
    billing_city = db.Column(db.String(140), default='')
    billing_country = db.Column(db.String(140), default='')

    def get_current_prices(self):
        return self.prices.order_by(Prices.start_date.desc()).first()

    def get_historical_prices(self,timestamp):
        for entry in self.prices:
            if entry.end_date == None:
                end = date.today()
            else:
                end = entry.end_date.date()
            print "timestamp: ", timestamp
            print "start: ", entry.start_date.date()
            print "end: ", end
            if timestamp >= entry.start_date.date() and entry.is_current():
                print "current"
                return entry
            elif timestamp >= entry.start_date.date() and timestamp < end:
                print "match"
                return entry
            else:
                print "no match"
        return None

    def get_prices(self):
        return Prices.query.filter(Prices.property_id == self.id).order_by(Prices.start_date.desc())

    def get_contracts(self):
        return Contract.query.join(Room).filter(Room.property_id == self.id)

    def get_all_datastreams(self):
        return Datastream.query.join(Feed).filter(Feed.property_id == self.id)

    def get_datastream_type(self,dataType):
        return Datastream.query.join(Feed).filter(Feed.property_id==self.id,Datastream.feed_id==Feed.id,Datastream.type==dataType).order_by(Datastream.info)

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

    def is_current(self):
        if self.end_date == None:
            return True
        else:
            return False

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

    def get_datastream_type(self,dataType):
        return self.datastreams.filter(Datastream.type==dataType)

class Feed(db.Model):
    __tablename__ = 'feed'
    id = db.Column(db.Integer, primary_key = True)
    xively_id = db.Column(db.Integer)
    api_key = db.Column(db.String(140))
    info = db.Column(db.String(140))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    datastreams = db.relationship('Datastream', backref = 'feed', lazy = 'dynamic', cascade="all, delete, delete-orphan")

    def get_type(self,dataType):
        return Datastream.query.filter(Datastream.feed_id == self.id,Datastream.type == dataType)

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

    def number_of_rooms(self):
        return rooms.count()
        
class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    user = db.relationship('User', backref="room_assoc")
    room = db.relationship('Room', backref="user_assoc")

    def is_current(self):
        if self.start_date.date() <= date.today() and self.end_date.date() >= date.today():
            return True
        else:
            return False

    def get_feeds(self):
        return Feed.query.join(Datastream,Room_Datastream).filter(self.room == Room_Datastream.room)

    def get_datastreams_per_feed(self,feed):
        return Datastream.query.join(Room_Datastream).filter(self.room == Room_Datastream.room,Datastream.feed_id == feed.id)

class Room_Datastream(db.Model):
    __tablename__ = 'room_datastream'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    datastream_id = db.Column(db.Integer, db.ForeignKey('datastream.id'))
    room = db.relationship('Room', backref="datastream_assoc")
    datastream = db.relationship('Datastream', backref="room_assoc")

def getUnit(datatype):
    if datatype == 2:
        return "m<sup>3</sup>"
    else:
        return "kWh"

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.String(500), default='')
    timestamp = db.Column(db.DateTime)
    read = db.Column(db.SmallInteger, default=0)

    def is_read(self):
        if self.read == 0:
            return False
        else:
            return True
