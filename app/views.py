from flask import render_template, flash, redirect, session, url_for, request, g, abort, Response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, facebook
from forms import LoginForm, EditForm, EditUserForm, EditPropertyForm, AddPropertyForm, UpdatePricesForm, EditPricesForm, AddRoomForm, EditRoomForm, AddFeedForm, AddDatastreamForm, AddUserContractForm, AddRoomContractForm, AddConnectionRoomDatastreamForm, AddConnectionDatastreamRoomForm, RequestPropertyForm, FeedbackForm
from models import User, ROLE_USER, ROLE_ADMIN, ROLE_LANDLORD, TYPE_ELECTRICITY, TYPE_ELECTRICITY_INST, TYPE_HEAT, TYPE_WATER, Property, Prices, Room, Feed, Datastream, Contract, Room_Datastream, getUnit, Feedback
from datetime import datetime, date
from xively import get_datastreams, get_dataset
from contract import get_usage_per_month, Month, Usage, get_last_week as get_last_week_values, get_last_month as get_last_month_values, get_last_year as get_last_year_values
from config import ADMIN_NAMES
from functools import wraps
from pdfs import create_pdf

#@app.route('/favicon.ico')
#def favicon():
#    return send_from_directory(os.path.join(app.root_path,'static'),'favicon.ico')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role != ROLE_ADMIN:
            flash("You need to be an admin to access this functionality")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def landlord_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role < ROLE_LANDLORD:
            flash("You need to be a landlord to access this functionality")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

#mimerender.register_mime('pdf',('application/pdf',))
#mimerender = mimerender.FlaskMimeRender(global_charset='UTF-8')

@lm.user_loader
def load_user(id):
    return User.query.get(id)

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@app.errorhandler(401)
def internal_error(error):
    return render_template('401.html'), 401

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page = 1):
    if request.method == "POST":
        dataType = int(request.form.get('dataType'))
    else:
        dataType = TYPE_ELECTRICITY
    if g.user.role == ROLE_USER:
        datastreams = g.user.get_datastream_type(dataType)
    elif g.user.role == ROLE_LANDLORD:
        datastreams = g.user.property.get_datastream_type(dataType)
    else:
        datastreams = None
    return render_template('index.html',
        title = 'Dashboard',
        datastreams = datastreams,
        dataType = dataType
        )

@app.route('/request_access', methods = ['GET', 'POST'])
@login_required
def request_access():
    if g.user.property_id != None:
        flash('You already have been assigned to a property. If this is incorrect, please contact your landlord or administrator')
        return redirect(url_for('index'))
    form = RequestPropertyForm()
    form.property.choices = [(p.id, p.name) for p in Property.query.order_by('name')]
    form.property.choices.insert(0,(0,None))
    if form.validate_on_submit():
        g.user.property_id = int(form.property.data)
        db.session.add(g.user)
        db.session.commit()
        flash('You have been assigned to property '+g.user.property.name)
        return redirect(url_for('index'))
    return render_template('request_access.html',
        form = form)



@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None or 'access_token' not in resp:
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))

    session['facebook_token'] = (resp['access_token'], '')

    data = facebook.get('/me').data
    if 'id' in data and 'name' in data:
        user_id = data['id']
        user_name = data['name']
    if 'email' in data:
        user_email = data['email']

    user = User.query.filter_by(facebook_id = user_id).first()

    if user is None:
        nickname = user_name
        nickname = User.make_unique_nickname(nickname)
        if user_name in ADMIN_NAMES:
            role = ROLE_ADMIN
        else:
            role = ROLE_USER
        user = User(nickname = nickname, email = user_email,facebook_id = user_id, role = role)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(request.args.get('next') or url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    return render_template('login.html', 
        title = 'Sign In',)
    
@app.route('/user/<nickname>', methods=['GET','POST'])
@login_required
def user(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        abort(404)
    contracts = Contract.query.filter_by(user = user)
    if request.method == "POST":
        dataType = int(request.form.get('dataType'))
    else:
        dataType = TYPE_ELECTRICITY
    datastreams = user.get_datastream_type(dataType)
    return render_template('user.html',
        user = user,
        contracts = contracts,
        ref = 'user',
        datastreams = datastreams,
        dataType = dataType
        )

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.street = form.street.data
        g.user.number = form.number.data
        g.user.postcode = form.postcode.data
        g.user.city = form.city.data
        g.user.country = form.country.data
        g.user.bank_IBAN = form.bank_IBAN.data
        g.user.bank_BIC = form.bank_BIC.data
        g.user.phone = form.phone.data
        g.user.phone_2 = form.phone_2.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user',nickname=g.user.nickname))
    elif request.method != "POST":
        form.nickname.data = g.user.nickname
        form.street.data = g.user.street
        form.number.data = g.user.number
        form.postcode.data = g.user.postcode
        form.city.data = g.user.city
        form.country.data = g.user.country
        form.bank_IBAN.data = g.user.bank_IBAN
        form.bank_BIC.data = g.user.bank_BIC
        form.phone.data = g.user.phone
        form.phone_2.data = g.user.phone_2
    return render_template('edit.html',
        form = form)

@app.route('/edit_user/<id>', methods = ['GET', 'POST'])
@login_required
#@admin_required
def edit_user(id):
    user = User.query.get(id)
    if user == None:
        flash("User not found")
        abort(404)

    form = EditUserForm()
    form.property.choices = [(p.id, p.name) for p in Property.query.order_by('name')]
    form.property.choices.insert(0,(0,None))
    form.role.choices = [(ROLE_USER,"user"),(ROLE_LANDLORD,"landlord"),(ROLE_ADMIN,"admin")]

    if form.validate_on_submit():
        if form.property.data != 0:
            user.property_id = form.property.data
        else:
            user.property_id = None
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('users'))
    return render_template('edit_user.html',
        user = user,
        form = form)


@app.route('/delete_user/<id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get(id)
    if user == None:
        flash('User not found')
        abort(404)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted')
    return redirect(url_for('users'))

@app.route('/users')
@login_required
#@admin_required
def users():
    users = User.query.all()
    return render_template('users.html',
        users = users)

@app.route('/properties')
@login_required
@admin_required
def properties():
    properties = Property.query.all()
    if properties == None:
        flash('No properties found.')
    return render_template('properties.html',
        properties = properties)

@app.route('/property/<id>', methods = ['GET','POST'])
@login_required
@landlord_required
def property(id):

    property = Property.query.get(id)

    if property == None:
        flash('Property not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != property.id:
            abort(401)

    contracts = property.get_contracts()
    if request.method == "POST":
        dataType = int(request.form.get('dataType'))
    else:
        dataType = TYPE_ELECTRICITY
    datastreams = property.get_datastream_type(dataType)
    return render_template('property.html',
        property = property,
        prices = property.get_current_prices(),
        rooms = property.rooms,
        feeds = property.feeds,
        contracts = contracts,
        users = property.users,
        datastreams = datastreams,
        dataType = dataType
        )

@app.route('/edit_property/<id>', methods = ['GET','POST'])
@login_required
@landlord_required
def edit_property(id):
    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != int(id):
            abort(401)

    property = Property.query.get(id)
    if property == None:
        flash('Property not found.')
        abort(404)
    
    form = EditPropertyForm(property.name)
    if form.validate_on_submit():
        property.name = form.name.data
        property.street = form.street.data
        property.number = form.number.data
        property.postcode = form.postcode.data
        property.city = form.city.data
        property.country = form.country.data
        property.bank_IBAN = form.bank_IBAN.data
        property.bank_BIC = form.bank_BIC.data
        property.vat_nr = form.vat_nr.data
        property.contact_name = form.contact_name.data
        property.contact_mail = form.contact_mail.data
        property.contact_phone = form.contact_phone.data
        property.billing_street = form.billing_street.data
        property.billing_number = form.billing_number.data
        property.billing_postcode = form.billing_postcode.data
        property.billing_city = form.billing_city.data
        property.billing_country = form.billing_country.data
        db.session.add(property)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('property', id = property.id))
    elif request.method != "POST":
        form.name.data = property.name
        form.street.data = property.street
        form.number.data = property.number
        form.postcode.data = property.postcode
        form.city.data = property.city
        form.country.data = property.country
        form.bank_IBAN.data = property.bank_IBAN
        form.bank_BIC.data = property.bank_BIC
        form.vat_nr.data = property.vat_nr
        form.contact_name.data = property.contact_name
        form.contact_mail.data = property.contact_mail
        form.contact_phone.data = property.contact_phone
        form.billing_street.data = property.billing_street
        form.billing_number.data = property.billing_number
        form.billing_postcode.data = property.billing_postcode
        form.billing_city.data = property.billing_city
        form.billing_country.data = property.billing_country
    return render_template('edit_property.html',
        propertyName = property.name,
        form = form)

@app.route('/add_property', methods = ['GET','POST'])
@login_required
@admin_required
def add_property():
    form = AddPropertyForm()
    if form.validate_on_submit():
        newProperty = Property(name=form.name.data)
        db.session.add(newProperty)
        db.session.commit()
        newProperty = Property.query.filter_by(name=form.name.data).first()
        newPrices = Prices(property = newProperty, start_date = datetime.utcnow())
        db.session.add(newPrices)
        db.session.commit()
        flash('New property '+newProperty.name+' added.')
        return redirect(url_for('properties'))
    return render_template('add_property.html',
        form = form)

@app.route('/delete_property/<id>')
@login_required
@admin_required
def delete_property(id):
    p = Property.query.get(id)
    if p == None:
        flash('Property not found.')
        abort(404)
    db.session.delete(p)
    db.session.commit()
    flash('Property deleted')
    return redirect(url_for('properties'))

@app.route('/update_prices/<id>', methods = ['GET','POST'])
@login_required
@landlord_required
def update_prices(id):
    prices = Prices.query.get(id)
    if prices == None:
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != prices.property_id:
            abort(401)

    form = UpdatePricesForm()
    if form.validate_on_submit():
        prices.end_date = datetime.utcnow()
        db.session.add(prices)
        newPrices = Prices(property = prices.property, start_date = datetime.utcnow(), electricity = int(form.electricity.data*100), heat = int(form.heat.data*100), water = int(form.water.data*100))
        db.session.add(newPrices)
        db.session.commit()
        flash('The prices for '+prices.property.name+' have been updated')
        return redirect(url_for('property', id = prices.property.id))
    elif request.method != "POST":
        form.electricity.data = float(prices.electricity)/100
        form.heat.data = float(prices.heat)/100
        form.water.data = float(prices.water)/100
    return render_template('update_prices.html',
        propertyName = prices.property.name,
        form = form)

@app.route('/prices/<id>')
@login_required
@landlord_required
def prices(id):
    p = Property.query.get(id)
    if p == None:
        flash('Property not found')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != int(id):
            abort(401)

    prices = p.get_prices()
    return render_template('prices.html',
        propertyName = p.name,
        prices = prices)

@app.route('/edit_prices/<id>', methods=['GET', 'POST'])
@login_required
@landlord_required
def edit_prices(id):
    p = Prices.query.get(id)
    if p == None:
        flash('Prices not found')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != p.property_id:
            abort(401)

    form = EditPricesForm()
    if form.validate_on_submit():
        p.electricity = int(form.electricity.data*100)
        p.heat = int(form.heat.data*100)
        p.water = int(form.water.data*100)
        p.start_date = form.start_date.data
        p.end_date = form.end_date.data
        db.session.add(p)
        db.session.commit()
        flash("Prices updated!")
        return redirect(url_for('prices',id=p.property_id))
    elif request.method != 'POST':
        form.electricity.data = float(p.electricity)/100
        form.heat.data = float(p.heat)/100
        form.water.data = float(p.water)/100
        form.start_date.data = p.start_date
        form.end_date.data = p.end_date
    return render_template('edit_prices.html',
        prices = p,
        form = form)

@app.route('/delete_prices/<id>')
@login_required
@landlord_required
def delete_prices(id):
    p = Prices.query.get(id)
    if p == None:
        flash('Prices not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != p.property_id:
            abort(401)

    db.session.delete(p)
    db.session.commit()
    flash('prices deleted')
    return redirect(url_for('prices',id=p.property_id))

@app.route('/add_room/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def add_room(id):
    property = Property.query.get(id)
    if property == None:
        flash('Property not found.')
        abort(404)
    form = AddRoomForm()
    if form.validate_on_submit():
        newRoom = Room(name=form.name.data,property=property,info=form.info.data)
        db.session.add(newRoom)
        db.session.commit()
        flash('New room "'+newRoom.name+'" was added to '+newRoom.property.name+'.')
        return redirect(url_for('room', id=newRoom.id))
    return render_template('add_room.html',
        form = form)

@app.route('/room/<id>', methods = ['GET', 'POST'])
@login_required
@landlord_required
def room(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != room.property_id:
            abort(401)

    contracts = Contract.query.filter_by(room = room)
    if request.method == "POST":
        dataType = int(request.form.get('dataType'))
    else:
        dataType = TYPE_ELECTRICITY
    datastreams = room.get_datastream_type(dataType)
    return render_template('room.html',
        contracts = contracts,
        connections = room.datastreams,
        datastreams = datastreams,
        dataType = dataType,
        room = room,
        ref = 'room'
        )

@app.route('/edit_room/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def edit_room(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)
    form = EditRoomForm()
    if form.validate_on_submit():
        room.name = form.name.data
        room.info = form.info.data
        db.session.add(room)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('room', id = id))
    elif request.method != "POST":
        form.name.data = room.name
        form.info.data = room.info
    return render_template('edit_room.html',
        room = room,
        form = form)

@app.route('/delete_room/<id>')
@login_required
@admin_required
def delete_room(id):
    r = Room.query.get(id)
    if r == None:
        flash('Room not found.')
        abort(404)
    property_id = r.property.id
    db.session.delete(r)
    db.session.commit()
    flash('Room deleted')
    return redirect(url_for('property',id= property_id))

@app.route('/add_feed/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def add_feed(id):
    property = Property.query.get(id)
    if property == None:
        flash('Property not found.')
        abort(404)
    form = AddFeedForm()
    if form.validate_on_submit():
        newFeed = Feed(xively_id=form.xively_id.data,api_key=form.api_key.data,property=property,info=form.info.data)
        db.session.add(newFeed)
        db.session.commit()
        xively_datastreams = get_datastreams(newFeed)
        if xively_datastreams != 'error':
            for i in range(0, len(xively_datastreams)):
                datastream_id = xively_datastreams[i]['id']
                j = 0
                datastream_tags = None
                while True:
                    try:
                        if datastream_tags == None:
                            datastream_tags = xively_datastreams[i]['tags'][j]
                        else:
                            datastream_tags += ', ' + xively_datastreams[i]['tags'][j]
                        j = j+1
                    except Exception, e:
                        break
                try:
                    datastream_unit = xively_datastreams[i]['unit']['label']
                except Exception, e:
                    datastream_unit = None
                newDatastream = Datastream(feed=newFeed,xively_id=datastream_id,unit=datastream_unit,info=datastream_tags)
                db.session.add(newDatastream)
            db.session.commit()
        else:
            flash('Automatic datastream lookup failed, please add manualy')
        flash('New feed "'+str(newFeed.xively_id)+'" was added to '+newFeed.property.name+'.')
        return redirect(url_for('feed', id=newFeed.id))
    return render_template('add_feed.html',
        form = form)

@app.route('/feed/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def feed(id):
    feed = Feed.query.get(id)
    if feed == None:
        flash('Feed not found.')
        abort(404)
    if request.method == "POST":
        dataType = int(request.form.get('dataType'))
    else:
        dataType = TYPE_ELECTRICITY
    datastreams = feed.get_type(dataType)
    return render_template('feed.html',
        feed = feed,
        datastreams = datastreams,
        dataType = dataType
        )

@app.route('/edit_feed/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def edit_feed(id):
    feed = Feed.query.get(id)
    if feed == None:
        flash('Feed not found.')
        abort(404)
    form = AddFeedForm() #edit form is equal to add form
    if form.validate_on_submit():
        feed.xively_id = form.xively_id.data
        feed.api_key = form.api_key.data
        feed.info = form.info.data
        db.session.add(feed)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('feed', id = id))
    elif request.method != "POST":
        form.xively_id.data = feed.xively_id
        form.api_key.data = feed.api_key
        form.info.data = feed.info
    return render_template('edit_feed.html',
        feed = feed,
        form = form)

@app.route('/delete_feed/<id>')
@login_required
@admin_required
def delete_feed(id):
    f = Feed.query.get(id)
    if f == None:
        flash('Feed not found.')
        abort(404)
    property_id = f.property.id
    db.session.delete(f)
    db.session.commit()
    flash('Feed deleted')
    return redirect(url_for('property',id= property_id))

@app.route('/add_datastream/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def add_datastream(id):
    feed = Feed.query.get(id)
    if feed == None:
        flash('Feed not found.')
        abort(404)
    form = AddDatastreamForm()
    form.type.choices = [(-1,'Select...'),(TYPE_ELECTRICITY_INST, 'Electricity Power'),(TYPE_ELECTRICITY, 'Electricity Cumulative'),(TYPE_HEAT, 'Heat'),(TYPE_WATER, 'Water')]
    if form.validate_on_submit():
        newDatastream = Datastream(xively_id=form.xively_id.data,feed=feed,info=form.info.data,unit=form.unit.data,type=form.type.data)
        db.session.add(newDatastream)
        db.session.commit()
        flash('New datastream "'+newDatastream.xively_id+'" was added to '+newDatastream.feed.xively_id+'.')
        return redirect(url_for('datastream', id=newDatastream.id))
    return render_template('add_datastream.html',
        form = form)

@app.route('/datastream/<id>')
@login_required
@admin_required
def datastream(id):
    datastream = Datastream.query.get(id)
    if datastream == None:
        flash('Datastream not found.')
        abort(404)
    datastreams = []
    datastreams.append(datastream)
    return render_template('datastream.html',
        datastream = datastream,
        datastreams = datastreams,
        rooms = datastream.rooms,
        )

@app.route('/_get_graph_data', methods=['POST'])
@login_required
def get_graph_data():
    datastream_id = request.form.get('datastream_id')
    zoom_level = request.form.get('zoom_level')
    timeStamp = request.form.get('timeStamp')
    
    datastream = Datastream.query.get(int(datastream_id))
    if datastream == None:
        flash ('Datastream not found')
        abort (404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != datastream.feed.property_id:
            abort(401)

    if zoom_level == None:
        zoom_level = 7
    zoom_level = int(zoom_level)

    dataset = get_dataset(datastream=datastream,zoom_level=zoom_level,timeStamp=timeStamp)
    return (dataset)

@app.route('/_get_last_week', methods=['POST'])
@login_required
def get_last_week():
    print "Fetching last week"
    room_id = request.form.get('room_id')
    datatype = int(request.form.get('datatype'))

    room = Room.query.get(int(room_id))
    if room == None:
        flash('Room not found')
        abort(404)
    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != datastream.feed.property_id:
            abort(401)

    datastreams=room.get_datastream_type(dataType=datatype)
    print "going to contract"
    value = get_last_week_values(datastreams=datastreams,property=room.property)
    print "back from contract"
    print value
    if datatype != 2:
        value = round(value/1000,2)
    else:
        value = round(value,2)
    value = str(value) + " " + getUnit(datatype=datatype)
    print value
    return value

@app.route('/_get_last_month', methods=['POST'])
@login_required
def get_last_month():
    room_id = request.form.get('room_id')
    datatype = int(request.form.get('datatype'))

    room = Room.query.get(int(room_id))
    if room == None:
        flash('Room not found')
        abort(404)
    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != datastream.feed.property_id:
            abort(401)

    datastreams=room.get_datastream_type(dataType=datatype)
    value = get_last_month_values(datastreams=datastreams,property=room.property)
    if datatype != 2:
        value = round(value/1000,2)
    else:
        value = round(value,2)
    value = str(value) + " " + getUnit(datatype=datatype)
    print value
    return value

@app.route('/_get_last_year', methods=['POST'])
@login_required
def get_last_year():
    room_id = request.form.get('room_id')
    datatype = int(request.form.get('datatype'))

    room = Room.query.get(int(room_id))
    if room == None:
        flash('Room not found')
        abort(404)
    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != datastream.feed.property_id:
            abort(401)

    datastreams=room.get_datastream_type(dataType=datatype)
    value = get_last_year_values(datastreams=datastreams,property=room.property)
    if datatype != 2:
        value = round(value/1000,2)
    else:
        value = round(value,2)
    value = str(value) + " " + getUnit(datatype=datatype)
    print value
    return value

@app.route('/edit_datastream/<id>', methods = ['GET','POST'])
@login_required
@admin_required
def edit_datastream(id):
    datastream = Datastream.query.get(id)
    if datastream == None:
        flash('Datastream not found.')
        abort(404)
    form = AddDatastreamForm()
    form.type.choices = [(-1,'Select...'),(TYPE_ELECTRICITY_INST, 'Electricity Power'),(TYPE_ELECTRICITY, 'Electricity Cumulative'),(TYPE_HEAT, 'Heat'),(TYPE_WATER, 'Water')]
    if form.validate_on_submit():
        datastream.xively_id = form.xively_id.data
        datastream.unit = form.unit.data
        datastream.info = form.info.data
        datastream.type = form.type.data
        db.session.add(datastream)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('datastream', id = id))
    elif request.method != "POST":
        form.xively_id.data = datastream.xively_id
        form.unit.data = datastream.unit
        form.info.data = datastream.info
    return render_template('edit_datastream.html',
        datastream = datastream,
        form = form)

@app.route('/delete_datastream/<id>')
@login_required
@admin_required
def delete_datastream(id):
    d = Datastream.query.get(id)
    if d == None:
        flash('Datastream not found')
        abort(404)
    feed_id = d.feed.id
    db.session.delete(d)
    db.session.commit()
    flash('Datastream deleted')
    return redirect(url_for('feed',id= feed_id))

@app.route('/add_user_contract/<id>', methods=['POST', 'GET'])
@login_required
@landlord_required
def add_user_contract(id):
    user = User.query.get(id)
    if user == None:
        flash('User not found.')
        abort(404)

    if user.property_id < 0:
        flash('User has to have a property first.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != user.property_id:
            abort(401)

    form = AddUserContractForm()
    form.room.choices = [(r.id, r.name) for r in user.property.rooms]
    form.room.choices.insert(0,(-1,'Select...'))
    if form.validate_on_submit():
        newContract = Contract(user=user,room_id=form.room.data,start_date=form.start_date.data,end_date=form.end_date.data)
        db.session.add(newContract)
        db.session.commit()
        flash('New contract between user '+newContract.user.nickname+' and room '+newContract.room.name+' was added.')
        return redirect(url_for('user', nickname=user.nickname))
    elif request.method != 'POST':
        form.start_date.data = datetime.utcnow()
        form.end_date.data = datetime.utcnow().replace(year=date.today().year+1)
    return render_template('add_user_contract.html',
        title = 'User Contract',
        user = user,
        form = form)

@app.route('/edit_user_contract/<id>', methods=['POST','GET'])
@login_required
@landlord_required
def edit_user_contract(id):
    contract = Contract.query.get(id)
    if contract == None:
        flash('contract not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != contract.room.property_id:
            abort(401)

    form = AddUserContractForm()
    form.room.choices = [(r.id, r.name) for r in contract.room.property.rooms if r.id != contract.room.id]
    form.room.choices.insert(0,(contract.room.id,contract.room.name))
    if form.validate_on_submit():
        contract.room_id = form.room.data
        contract.start_date = form.start_date.data
        contract.end_date = form.end_date.data
        db.session.add(contract)
        db.session.commit()
        flash('Changes saved!')
        return redirect(url_for('user', nickname=contract.user.nickname))
    elif request.method != 'POST':
        form.start_date.data = contract.start_date
        form.end_date.data = contract.end_date
    return render_template('edit_user_contract.html',
        title = 'User Contract',
        contract = contract,
        user = contract.user,
        form = form)

@app.route('/add_room_contract/<id>', methods=['POST', 'GET'])
@login_required
@landlord_required
def add_room_contract(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != room.property_id:
            abort(401)

    form = AddRoomContractForm()
    form.user.choices = [(u.id, u.nickname) for u in room.property.users]
    form.user.choices.insert(0,(-1,'Select...'))
    if form.validate_on_submit():
        newContract = Contract(user_id=form.user.data,room=room,start_date=form.start_date.data,end_date=form.end_date.data)
        db.session.add(newContract)
        db.session.commit()
        flash('New contract between user '+newContract.user.nickname+' and room '+newContract.room.name+' was added.')
        return redirect(url_for('room', id=room.id))
    elif request.method != 'POST':
        form.start_date.data = datetime.utcnow()
        form.end_date.data = datetime.utcnow().replace(year=date.today().year+1)
    return render_template('add_room_contract.html',
        title = 'Room Contract',
        room = room,
        form = form)

@app.route('/edit_room_contract/<id>', methods=['POST','GET'])
@login_required
@landlord_required
def edit_room_contract(id):
    contract = Contract.query.get(id)
    if contract == None:
        flash('contract not found.')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != contract.room.property_id:
            abort(401)

    form = AddRoomContractForm()
    form.user.choices = [(u.id, u.nickname) for u in contract.room.property.users if u.id != contract.user.id]
    form.user.choices.insert(0,(contract.user.id,contract.user.nickname))
    if form.validate_on_submit():
        contract.user_id = form.user.data
        contract.start_date = form.start_date.data
        contract.end_date = form.end_date.data
        db.session.add(contract)
        db.session.commit()
        flash('Changes saved!')
        return redirect(url_for('room', id=contract.room.id))
    elif request.method != 'POST':
        form.start_date.data = contract.start_date
        form.end_date.data = contract.end_date
    return render_template('edit_room_contract.html',
        title = 'Room Contract',
        contract = contract,
        room = contract.room,
        form = form)

@app.route('/delete_contract/<id>')
@login_required
@landlord_required
def delete_contract(id):
    c = Contract.query.get(id)
    if c == None:
        flash('contract not found')
        abort(404)

    if g.user.role != ROLE_ADMIN:
        if g.user.property_id != c.room.property_id:
            abort(401)

    db.session.delete(c)
    db.session.commit()
    flash('Contract deleted')
    return redirect('index')

@app.route('/contract_detail/<id>')
@login_required
def contract_detail(id):
    c = Contract.query.get(id)
    if c == None:
        flash('contract not found')
        abort(404)

    if g.user.role == ROLE_LANDLORD:
        if g.user.property_id != c.room.property_id:
            abort(401)
    if g.user.role == ROLE_USER:
        if g.user != c.user:
            abort(401)

    monthly_values = get_usage_per_month(datastreams=c.room.datastreams,start=c.start_date,end=c.end_date,property=c.room.property)

    return render_template('contract_detail.html',
        contract = c,
        user = c.user,
        property = c.room.property,
        room = c.room,
        months = monthly_values
        )

@app.route('/pdf_contract/<id>/<start_date>/<end_date>.pdf')
@login_required
def pdf_contract(id,start_date,end_date):
    c = Contract.query.get(id)
    if c == None:
        flash('contract not found')
        abort(404)

    if g.user.role == ROLE_LANDLORD:
        if g.user.property_id != c.room.property_id:
            abort(401)
    if g.user.role == ROLE_USER:
        if g.user != c.user:
            abort(401)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    values = get_usage_per_month(datastreams=c.room.datastreams,start=start,end=end,property=c.room.property)[0]

    pdf = create_pdf(render_template('pdf_contract.html',contract = c,user=c.user,property=c.room.property,room=c.room,month=values))
    return Response(pdf, mimetype='application/pdf')

@app.route('/add_connection_room_datastream/<id>', methods=['POST', 'GET'])
@login_required
@admin_required
def add_connection_room_datastream(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)
    form = AddConnectionRoomDatastreamForm()
    form.datastream.choices = [(d.id, (d.xively_id+": "+d.info)) for d in room.property.get_all_datastreams()]
    form.datastream.choices.insert(0,(-1,'Select...'))
    if form.validate_on_submit():
        newConnection = Room_Datastream(datastream_id=form.datastream.data,room=room)
        db.session.add(newConnection)
        db.session.commit()
        flash('New connection between datastream '+newConnection.datastream.xively_id+' and room '+newConnection.room.name+' was added.')
        return redirect(url_for('room', id=room.id))
    return render_template('add_connection_room_datastream.html',
        room = room,
        form = form)

@app.route('/edit_connection_room_datastream/<id>', methods=['POST','GET'])
@login_required
@admin_required
def edit_connection_room_datastream(id):
    connection = Room_Datastream.query.get(id)
    if connection == None:
        flash('connection not found.')
        abort(404)
    form = AddConnectionRoomDatastreamForm()
    form.datastream.choices = [(d.id, (d.xively_id+": "+d.info)) for d in connection.room.property.get_all_datastreams() if d.id != connection.datastream.id]
    form.datastream.choices.insert(0,(connection.datastream.id,(connection.datastream.xively_id+": "+connection.datastream.info)))
    if form.validate_on_submit():
        connection.datastream_id = form.datastream.data
        db.session.add(connection)
        db.session.commit()
        flash('Changes saved!')
        return redirect(url_for('room', id=connection.room.id))
    return render_template('edit_connection_room_datastream.html',
        connection = connection,
        room = connection.room,
        form = form)

@app.route('/add_connection_datastream_room/<id>', methods=['POST', 'GET'])
@login_required
@admin_required
def add_connection_datastream_room(id):
    datastream = Datastream.query.get(id)
    if datastream == None:
        flash('Datastream not found.')
        abort(404)
    form = AddConnectionDatastreamRoomForm()
    form.room.choices = [(r.id, r.name) for r in datastream.feed.property.rooms]
    form.room.choices.insert(0,(-1,'Select...'))
    if form.validate_on_submit():
        newConnection = Room_Datastream(datastream=datastream,room_id=form.room.data)
        db.session.add(newConnection)
        db.session.commit()
        flash('New connection between datastream '+newConnection.datastream.xively_id+' and room '+newConnection.room.name+' was added.')
        return redirect(url_for('datastream', id=datastream.id))
    return render_template('add_connection_datastream_room.html',
        datastream = datastream,
        form = form)

@app.route('/edit_connection_datastream_room/<id>', methods=['POST','GET'])
@login_required
@admin_required
def edit_connection_datastream_room(id):
    connection = Room_Datastream.query.get(id)
    if connection == None:
        flash('connection not found.')
        abort(404)
    form = AddConnectionDatastreamRoomForm()
    form.room.choices = [(r.id, r.name) for r in connection.datastream.feed.property.rooms if r.id != connection.room.id]
    form.room.choices.insert(0,(connection.room.id,connection.room.name))
    if form.validate_on_submit():
        connection.room_id = form.room.data
        db.session.add(connection)
        db.session.commit()
        flash('Changes saved!')
        return redirect(url_for('datastream', id=connection.datastream.id))
    return render_template('edit_connection_datastream_room.html',
        connection = connection,
        datastream = connection.datastream,
        form = form)

@app.route('/delete_room_datastream/<id>')
@login_required
@admin_required
def delete_room_datastream(id):
    c = Room_Datastream.query.get(id)
    if c == None:
        flash('Connection not found')
        abort(404)
    db.session.delete(c)
    db.session.commit()
    flash('Connection deleted')
    return redirect('index')

@app.route('/read_feedback')
@login_required
@admin_required
def read_feedback():
    feedback = Feedback.query.order_by(Feedback.timestamp.desc())
    return render_template('read_feedback.html',
        feedback = feedback)

@app.route('/send_feedback', methods=['GET', 'POST'])
@login_required
def send_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        newFeedback = Feedback(sender=g.user,text=form.text.data, timestamp=datetime.utcnow())
        db.session.add(newFeedback)
        db.session.commit()
        flash('Your feedback has been submitted! Thank you!')
        return redirect(url_for('index'))
    return render_template('send_feedback.html',
        form = form)
