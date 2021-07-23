from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, ProductSearchForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from turbo_flask import Turbo
from flask_behind_proxy import FlaskBehindProxy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required
from flask_login import logout_user, current_user
from queryproduct import parse_data, find_alts, get_product_info
from queryproduct import get_trending_items
import pandas as pd

# this gets the name of the file so Flask knows it's name
app = Flask(__name__)
proxied = FlaskBehindProxy(app)

app.config['SECRET_KEY'] = '56f662178b6ca0617379a38e5b857cee'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bcrypt = Bcrypt(app)
turbo = Turbo(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.password}')"


class SavedItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    items = db.Column(db.String(920), unique=True, nullable=False)

    def __repr__(self):
        return f"Items('{self.username}', '{self.items}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # checks if entries are valid
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=bcrypt.generate_password_hash(
                form.password.data).decode('utf-8'))
        try:
            db.session.add(user)
            db.session.commit()
        except exc.IntegrityError:
            flash(
                'User not created: Username or email associated' +
                ' with existing account', 'error')
        else:
            flash(f'Account created for {form.username.data}!', 'success')
        finally:
            return redirect(url_for('init'))  # if so - send to home page
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        my_user = db.session.query(User).filter_by(
            username=form.username.data).first()
        if my_user:
            if bcrypt.check_password_hash(
                    my_user.password, form.password.data):
                flash(f'Succesfully logged in', 'success')
                login_user(my_user, remember=form.remember.data)
                return redirect(url_for('init'))
            else:
                flash('Incorrect password', 'error')
                return redirect(url_for('init'))
        else:
            flash('User does not exist', 'error')
            return redirect(url_for('init'))
    return render_template('login.html', title='Login', form=form)


@app.route("/about")
@login_required
def about():
    return render_template('about.html', subtitle='About Page')


# Old home
# @app.route("/home")
# @login_required
# def home():
#     return render_template('home.html', subtitle='Home Page')

@app.route("/")
@app.route("/home")
def init():
    try:
        json = get_trending_items()
        itemItemDict = {}
        if 'results' in json:
            results = json['results']
            i = 0
            for item in results:
                itemDict = {}
                itemDict['name'] = item['names']['title']
                itemDict['pic'] = item['images']['standard']
                print(itemDict['pic'])
                itemDict['sku'] = item['sku']
                itemItemDict[i] = itemDict
                i = i + 1

        itemItemDict['size'] = len(itemItemDict)
        print(itemItemDict['size'])
        return render_template('home.html', trending=itemItemDict)
    except Exception as e:
        print(e)
    finally:
        print('yo')


@app.route("/logout")
@login_required
def logout():
    logout_user
    return redirect(url_for('login'))


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search = ProductSearchForm()
    if request.method == 'POST':
        if search.data['search']:
            return search_results(search)
        else:
            flash('Field cannot be blank')
            return redirect(url_for('search'))

    return render_template('search.html', form=search)


@app.route('/results')
def search_results(search):
    results = parse_data(search.data['search'])

    return render_template(
        'results.html',
        tables=[
            results.to_html(
                header="true",
                escape=False)])


# we don't need this rn
#
# @app.route('/saved-items')
# def savedItems():
#     try:
#         userItems = SavedItems.query.filter_by(username='arihamilton')\
#         .first() # replace with name of current user
#         itemItemDict = {}
#         if userItems:
#             strItems = str(userItems.items)
#             itemSKUs = strItems.split(" ")
#             for item in itemSKUs:
#                 json = get_product_info(item)

#                 itemDict = {}
#                 itemDict['pic'] = json['image']
#                 itemDict['name'] = json['name']
#                 itemDict['startDate'] = json['startDate']
#                 itemDict['price'] = json['regularPrice']
#                 itemDict['salePrice'] = json['salePrice']
#                 itemItemDict[str(item)] = itemDict

#         return render_template('products.html', products=itemItemDict)
#     except Exception as e:
#         print(e)
#     finally:
#         print('yo')

@app.route('/item/<sku>')
def show_item_page(sku):
    try:
        json = get_product_info(sku)
        itemDict = {}
        alternatives = {}
        if json:
            itemDict['name'] = json['name']
            itemDict['pic'] = json['image']
            itemDict['startDate'] = json['startDate']
            itemDict['price'] = json['regularPrice']
            itemDict['salePrice'] = json['salePrice']
            itemDict['rating'] = json['customerReviewAverage']
            itemDict['description'] = json['longDescription']
            itemDict['addToCart'] = json['addToCartUrl']

            alts = find_alts(sku, json['salePrice'])
            if not alts.empty:
                for row in alts.itertuples():
                    print(row[1])
                    inf = get_product_info(row[1])
                    altDict = {}
                    altDict['name'] = inf['name']
                    altDict['pic'] = inf['image']
                    altDict['price'] = inf['salePrice']
                    cart_url = inf['addToCartUrl']
                    altDict['addToCartUrl'] = cart_url
                    altDict['sku'] = inf['sku']

                    alternatives[row.Index] = altDict

        return render_template(
            'item.html',
            item=itemDict,
            alternatives=alternatives)
    except Exception as e:
        print(e)
    finally:
        print('yo')


if __name__ == '__main__':               # this should always be at the end
    app.run(debug=True, host="0.0.0.0")
