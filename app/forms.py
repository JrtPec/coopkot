from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, HiddenField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired as Required
from wtforms.validators import Length, optional, NumberRange
from models import User, Property, Prices, Room

class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
    
class EditForm(Form):
    nickname = HiddenField('nickname', validators = [Required()])
    email = HiddenField('email', validators = [Length(min = 0, max = 120)])
    phone = TextField('phone', validators = [Length(min = 0, max = 140)])
    phone_2 = TextField('phone2', validators = [Length(min = 0, max = 140)])
    bank_IBAN = TextField('bank_IBAN', validators = [Length(min = 0, max = 140)])
    bank_BIC = TextField('bank_BIC', validators = [Length(min = 0, max = 140)])
    street = TextField('street', validators = [Length(min = 0, max = 140)])
    number = TextField('number', validators = [Length(min = 0, max = 140)])
    postcode = TextField('postcode', validators = [Length(min = 0, max = 140)])
    city = TextField('city', validators = [Length(min = 0, max = 140)])
    country = TextField('country', validators = [Length(min = 0, max = 140)])

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

class EditUserForm(Form):
    property = SelectField('property', coerce=int, validators=[optional()])
    role = SelectField('role', coerce=int, validators=[optional()])

class EditPropertyForm(Form):
    name = TextField('name', validators = [Required()])
    street = TextField('street', validators = [Length(min = 0, max = 140)])
    number = TextField('number', validators = [Length(min = 0, max = 140)])
    postcode = TextField('postcode', validators = [Length(min = 0, max = 140)])
    city = TextField('city', validators = [Length(min = 0, max = 140)])
    country = TextField('country', validators = [Length(min = 0, max = 140)])
    bank_IBAN = TextField('bank_IBAN', validators = [Length(min = 0, max = 140)])
    bank_BIC = TextField('bank_BIC', validators = [Length(min = 0, max = 140)])
    vat_nr = TextField('vat_nr', validators = [Length(min = 0, max = 140)])
    contact_name = TextField('contact_name', validators = [Length(min = 0, max = 140)])
    contact_mail = TextField('contact_mail', validators = [Length(min = 0, max = 140)])
    contact_phone = TextField('contact_phone', validators = [Length(min = 0, max = 140)])
    billing_street = TextField('billing_street', validators = [Length(min = 0, max = 140)])
    billing_number = TextField('billing_number', validators = [Length(min = 0, max = 140)])
    billing_postcode = TextField('billing_postcode', validators = [Length(min = 0, max = 140)])
    billing_city = TextField('billing_city', validators = [Length(min = 0, max = 140)])
    billing_country = TextField('billing_country', validators = [Length(min = 0, max = 140)])

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
    type = SelectField('type', coerce=int, validators=[NumberRange(min=0, message='Select a valid type')])

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

class RequestPropertyForm(Form):
    property = SelectField('property', coerce=int, validators=[Required()])