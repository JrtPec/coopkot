from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, HiddenField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired as Required
from wtforms.validators import Length, optional
from models import User, Property, Prices, Room

class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
    
class EditForm(Form):
    nickname = TextField('nickname', validators = [Required()])
    property = SelectField('property', coerce=int, validators=[optional()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])
    
    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname
        
    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname = self.nickname.data).first()
        if user != None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True

class EditPropertyForm(Form):
    name = TextField('name', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

    def __init__(self, original_name, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_name = original_name
        
    def validate(self):
        if not Form.validate(self):
            return False
        if self.name.data == self.original_name:
            return True
        property = Property.query.filter_by(name = self.name.data).first()
        if property != None:
            self.name.errors.append('This name is already in use. Please choose another one.')
            return False
        return True

class AddPropertyForm(Form):
    name = TextField('name', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

    def validate(self):
        if not Form.validate(self):
            return False
        property = Property.query.filter_by(name = self.name.data).first()
        if property != None:
            self.name.errors.append('This name is already in use. Please choose another one.')
            return False
        return True

class UpdatePricesForm(Form):
    electricity = DecimalField('electricity', validators = [Required()], places = 2)
    heat = DecimalField('heat', validators = [Required()], places = 2)
    water = DecimalField('water', validators = [Required()], places = 2)

class EditPricesForm(Form):
    electricity = DecimalField('electricity', validators = [Required()], places = 2)
    heat = DecimalField('heat', validators = [Required()], places = 2)
    water = DecimalField('water', validators = [Required()], places = 2)
    start_date = DateField('start_date', validators=[Required()])
    end_date = DateField('end_date')

class AddRoomForm(Form):
    name = TextField('name', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

class EditRoomForm(Form):
    name = TextField('name', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

class AddFeedForm(Form):
    xively_id = TextField('xively_id', validators = [Required()])
    api_key = TextField('api_key', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

class AddDatastreamForm(Form):
    xively_id = TextField('xively_id', validators = [Required()])
    unit = TextField('unit', validators = [Required()])
    info = TextAreaField('info', validators = [Length(min = 0, max = 140)])

class AddUserContractForm(Form):
    room = SelectField('room', coerce=int, validators=[Required()])
    start_date = DateField('start_date', validators=[Required()])
    end_date = DateField('end_date', validators=[Required()])

class AddRoomContractForm(Form):
    user = SelectField('user', coerce=int, validators=[Required()])
    start_date = DateField('start_date', validators=[Required()])
    end_date = DateField('end_date', validators=[Required()])

class AddConnectionRoomDatastreamForm(Form):
    datastream = SelectField('datastream', coerce=int, validators=[Required()])

class AddConnectionDatastreamRoomForm(Form):
    room = SelectField('room', coerce=int, validators=[Required()])