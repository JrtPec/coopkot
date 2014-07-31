from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, facebook
from forms import LoginForm, EditForm, EditPropertyForm, AddPropertyForm, UpdatePricesForm, AddRoomForm, EditRoomForm, AddFeedForm, AddDatastreamForm, AddUserContractForm, AddRoomContractForm, AddConnectionRoomDatastreamForm, AddConnectionDatastreamRoomForm
from models import User, ROLE_USER, ROLE_ADMIN, ROLE_LANDLORD, Property, Prices, Room, Feed, Datastream, Contract, Room_Datastream
from datetime import datetime, date
from xively import get_datastreams, get_dataset

#@app.route('/favicon.ico')
#def favicon():
#    return send_from_directory(os.path.join(app.root_path,'static'),'favicon.ico')

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
    return render_template('index.html',
        title = 'Dashboard',
        )

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized/<resp>")
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

    user = User.query.filter_by(facebook_id = user_id).first()

    if user is None:
        nickname = user_name
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname = nickname, facebook_id = user_id, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(request.args.get('next') or url_for('index'))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    return render_template('login.html', 
        title = 'Sign In',)
    
@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        abort(404)
    contracts = Contract.query.filter_by(user = user)
    return render_template('user.html',
        user = user,
        contracts = contracts,
        ref = 'user'
        )

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    form.property.choices = [(p.id, p.name) for p in Property.query.order_by('name')]
    form.property.choices.insert(0,(-1,None))
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.property_id = form.property.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user',nickname=g.user.nickname))
    elif request.method != "POST":
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html',
        form = form)

@app.route('/users')

def users():
    print "Querying all users"
    users = User.query.all()
    print "Creating new user"
    user = User(nickname = 'Jan', email='jan@jan.be')
    print "Adding user to session"
    db.session.add(user)
    print "Committing.."
    db.session.commit()
    print "Rendering"
    return render_template('users.html',
        users = users)

@app.route('/properties')
@login_required
def properties():
    properties = Property.query.all()
    if properties == None:
        flash('No properties found.')
    return render_template('properties.html',
        properties = properties)

@app.route('/property/<id>')
@login_required
def property(id):
    property = Property.query.get(id)
    contracts = property.get_contracts()
    if property == None:
        flash('Property not found.')
        abort(404)
    return render_template('property.html',
        property = property,
        prices = property.get_current_prices(),
        rooms = property.rooms,
        feeds = property.feeds,
        contracts = contracts,
        users = property.users
        )

@app.route('/edit_property/<id>', methods = ['GET','POST'])
@login_required
def edit_property(id):
    property = Property.query.get(id)
    if property == None:
        flash('Property not found.')
        abort(404)
    form = EditPropertyForm(property.name)
    if form.validate_on_submit():
        property.name = form.name.data
        property.info = form.info.data
        db.session.add(property)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('property', id = property.id))
    elif request.method != "POST":
        form.name.data = property.name
        form.info.data = property.info
    return render_template('edit_property.html',
        propertyName = property.name,
        form = form)

@app.route('/add_property', methods = ['GET','POST'])
@login_required
def add_property():
    form = AddPropertyForm()
    if form.validate_on_submit():
        newProperty = Property(name=form.name.data,info=form.info.data)
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
def update_prices(id):
    prices = Prices.query.get(id)
    if prices == None:
        abort(404)
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

@app.route('/add_room/<id>', methods = ['GET','POST'])
@login_required
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

@app.route('/room/<id>')
@login_required
def room(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)
    contracts = Contract.query.filter_by(room = room)
    return render_template('room.html',
        contracts = contracts,
        datastreams = room.datastreams,
        room = room,
        ref = 'room'
        )

@app.route('/edit_room/<id>', methods = ['GET','POST'])
@login_required
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

@app.route('/feed/<id>')
@login_required
def feed(id):
    feed = Feed.query.get(id)
    if feed == None:
        flash('Feed not found.')
        abort(404)
    return render_template('feed.html',
        feed = feed
        )

@app.route('/edit_feed/<id>', methods = ['GET','POST'])
@login_required
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
def add_datastream(id):
    feed = Feed.query.get(id)
    if feed == None:
        flash('Feed not found.')
        abort(404)
    form = AddDatastreamForm()
    if form.validate_on_submit():
        newDatastream = Datastream(xively_id=form.xively_id.data,feed=feed,info=form.info.data,unit=form.unit.data)
        db.session.add(newDatastream)
        db.session.commit()
        flash('New datastream "'+newDatastream.xively_id+'" was added to '+newDatastream.feed.xively_id+'.')
        return redirect(url_for('datastream', id=newDatastream.id))
    return render_template('add_datastream.html',
        form = form)

@app.route('/datastream/<id>')
@login_required
def datastream(id):
    datastream = Datastream.query.get(id)
    if datastream == None:
        flash('Datastream not found.')
        abort(404)
    dataset = get_dataset(datastream)
    print dataset
    return render_template('datastream.html',
        datastream = datastream,
        rooms = datastream.rooms,
        dataset = get_dataset(datastream)
        )

@app.route('/edit_datastream/<id>', methods = ['GET','POST'])
@login_required
def edit_datastream(id):
    datastream = Datastream.query.get(id)
    if datastream == None:
        flash('Datastream not found.')
        abort(404)
    form = AddDatastreamForm()
    if form.validate_on_submit():
        datastream.xively_id = form.xively_id.data
        datastream.unit = form.unit.data
        datastream.info = form.info.data
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
def add_user_contract(id):
    user = User.query.get(id)
    if user == None:
        flash('User not found.')
        abort(404)
    if user.property_id < 0:
        flash('User has to have a property first.')
        abort(404)
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
def edit_user_contract(id):
    contract = Contract.query.get(id)
    if contract == None:
        flash('contract not found.')
        abort(404)
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
def add_room_contract(id):
    room = Room.query.get(id)
    if room == None:
        flash('Room not found.')
        abort(404)
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
def edit_room_contract(id):
    contract = Contract.query.get(id)
    if contract == None:
        flash('contract not found.')
        abort(404)
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
def delete_contract(id):
    c = Contract.query.get(id)
    if c == None:
        flash('contract not found')
        abort(404)
    db.session.delete(c)
    db.session.commit()
    flash('Contract deleted')
    return redirect('index')

@app.route('/add_connection_room_datastream/<id>', methods=['POST', 'GET'])
@login_required
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
def delete_room_datastream(id):
    c = Room_Datastream.query.get(id)
    if c == None:
        flash('Connection not found')
        abort(404)
    db.session.delete(c)
    db.session.commit()
    flash('Connection deleted')
    return redirect('index')