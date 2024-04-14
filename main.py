from flask import Flask, render_template, url_for,request,flash,redirect
from flask_login import UserMixin,current_user,login_user,logout_user,login_required,LoginManager
from flask_sqlalchemy import  SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash,check_password_hash
import secrets

def secret_key():
    token = secrets.token_hex(10)
    return token

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = secret_key()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///account.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True,nullable = False)
    email = db.Column(db.String(150), unique=True,nullable = False)
    image_file = db.Column(db.String(20),nullable = False,default='default.jpg')
    password = db.Column(db.String(150),nullable = False)
    posts = db.relationship('Post',backref = 'author',lazy=True)
    #backref used to get the author

    def __repr__(self):
        return f"User('{self.username}','{self.email}','{self.image_file}')"

class Post(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(10000),nullable = False)
    date_posted = db.Column(db.DateTime(timezone=True),default = func.now())
    content = db.Column(db.Text,nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"
posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First Post Content',
        'date_posted': 'April 20,2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 20,2018'
    }
]

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html", posts=posts,user = current_user)


@app.route('/about')
def about():
    return render_template("about.html", title="About",user = current_user)


@app.route('/register',methods = ["GET","POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if len(email) < 4:
            flash('Email must be greater than 4 characters', 'error')
        elif len(username) < 2:
            flash('Firstname must be greater than 1 characters', 'error')
        elif password1 != password2:
            flash('Password mismatch', 'error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters','error')
        else:
            flash(f'Account Created for {username}!','success')
            user = User.query.filter_by(email=email).first()
            return redirect(url_for("home"))
    return render_template('register.html', title='Register',user = current_user)


@app.route('/login',methods = ["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password1')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash(f"Logged in Successfully", category="success",user = current_user)
                login_user(user, remember=True)
                return redirect(url_for("home"))

            else:
                flash("Password Incorrect", category="error")
        else:
            flash("User does not exist", category="error")
    return render_template('login.html', title='Login')

if __name__ == "__main__":
    app.run(debug=True)