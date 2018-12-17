from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, BooksMenu ,User
from flask import session as login_session
import random
import string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "item Catalog"


# Connect to Database and create database session
engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    #create user when recieve information form google api
    user_id=getUserID(login_session['email'])
    if not user_id:
    	user_id=createUser(login_session)
    else:
    	login_session['user_id']=user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output




def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session[
               'email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id




def getUserInfo(user_id):

	user = session.query(User).filter_by(id=user_id).one()
	return user
    

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        return redirect(url_for('catalog'))
        
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

        return None



@app.route('/')
@app.route('/catalog/')
def catalog():
	categories=session.query(Categories).all()
	books=session.query(BooksMenu).order_by(BooksMenu.id.desc()).limit(10)
	if 'username' not in login_session:
		return render_template('publicCatalog.html',categories=categories,books=books)
	else:
		return render_template('catalog.html',categories=categories , books=books)

#JSON FOR Categories end point
@app.route('/json/')
@app.route('/catalog/json/')
def categoriesJson():
	categories=session.query(Categories).all()
	return jsonify(Categories=[i.serialize for i in categories])


@app.route('/catalog/new/',methods=['GET','POST'])
def newBook():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newBook=BooksMenu(
			name=request.form['name'],description=request.form['description'],rating=request.form['rating'],
			category_id=request.form['category_id'],user_id=login_session['user_id']
			)
		session.add(newBook)
		session.commit()
		flash("new Book created")
		return redirect(url_for('catalog'))

	else:
		return render_template('newBook.html')

@app.route('/catalog/<int:category_id>/')
def booksMenu(category_id):
	allCategories=session.query(Categories).all()
	categories=session.query(Categories).filter_by(id=category_id).one()
	books=session.query(BooksMenu).filter_by(category_id=category_id)
	return render_template('booksMenu.html',allCategories=allCategories, categories=categories,
							books=books )

	
#json for Menu end point
@app.route('/catalog/<int:category_id>/json/')
def booksMenuJson(category_id):
	category=session.query(Categories).filter_by(id=category_id).one()
	books=session.query(BooksMenu).filter_by(category_id= category_id).all()
	return jsonify(BooksMenu=[i.serialize for i in books])


@app.route('/catalog/<int:category_id>/<int:book_id>/')
def showBook(category_id,book_id):
	categories=session.query(Categories).filter_by(id=category_id).one()
	books=session.query(BooksMenu).filter_by(id=book_id).one()
	if 'username' not in login_session or books.user_id != login_session['user_id']:
			return render_template('publicBook.html',categories=categories,
									books=books)
	else:
		return render_template('book.html',categories=categories,books=books)

@app.route('/catalog/<int:category_id>/<int:book_id>/json')
def showBookJson(category_id,book_id):
	categories = session.query(Categories).filter_by(id=category_id).one()
	books=session.query(BooksMenu).filter_by(id=book_id)
	return jsonify(BookDetails=[i.serialize for i in books])


@app.route('/catalog/<int:category_id>/<int:book_id>/edit/',methods=['GET','POST'])
def editBook(category_id,book_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedBook=session.query(BooksMenu).filter_by(id=book_id).one()
	if login_session['user_id'] != editedBook.user_id:
		return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own Book Menu in order to edit.');}</script><body onload='myFunction()''>"
	if request.method =='POST':
		if request.form['name']:
			editedBook.name=request.form['name']
			editedBook.description=request.form['description']
			editedBook.rating=request.form['rating']
			session.add(editedBook)
			session.commit()
			flash('Book edited Successfully')
			return redirect(url_for('booksMenu',category_id=category_id,book_id =book_id))
		

	else:
		return render_template('editBook.html',category_id=category_id,book_id=book_id,
								book=editedBook)

@app.route('/catalog/<int:category_id>/<int:book_id>/delete/',methods=['GET','POST'])
def deleteBook(category_id,book_id):
	if 'username' not in login_session:
		return redirect('/login')
	deletedBook=session.query(BooksMenu).filter_by(id=book_id).one()
	if deletedBook.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own Book Menu in order to delete.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		session.delete(deletedBook)
		session.commit()
		flash("Book deleted Successfully!")
		return redirect(url_for('booksMenu',category_id=category_id))

	else:
		return render_template('deleteBook.html',category_id=category_id,book_id=book_id,
								book=deletedBook)

if __name__== '__main__':
	app.secret_key='super_secret_key'
	app.debug=True
	app.run(host="0.0.0.0",port=5000)