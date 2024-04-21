from flask import Flask, render_template, url_for, request, flash, redirect, jsonify, abort
from flask_login import UserMixin, current_user, login_user, logout_user, login_required, LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import json


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


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(150), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    # backref used to get the author

    def __repr__(self):
        return f"User('{self.username}','{self.email}','{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10000), nullable=False)
    date_posted = db.Column(db.DateTime(timezone=True), default=func.now())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"
    
    
@app.route('/')
@app.route('/home')
def home():
    #posts = Post.query.all() -> To query all pages
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template("home.html", posts=posts, user=current_user)


@app.route('/about')
def about():
    return render_template("about.html", title="About", user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        user = User.query.filter_by(email=email).first()
        username_match = User.query.filter_by(username=username).first()
        
        if user:
            flash("Email already exists.", category="error")
        elif username_match:
            flash("Username already taken.", category="error")
        elif len(email) < 4:
            flash('Email must be greater than 4 characters', 'error')
        elif len(username) < 2:
            flash('Firstname must be greater than 1 characters', 'error')
        elif password1 != password2:
            flash('Password mismatch', 'error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters', 'error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created', category='success')
            return redirect(url_for('home'))
    return render_template('register.html', title='Register', user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password1')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash(f"Logged in Successfully", category="success")
                login_user(user, remember=True)
                return redirect(url_for("home"))

            else:
                flash("Password Incorrect", category="error")
        else:
            flash("User does not exist", category="error")
    return render_template('login.html', title='Login', user=current_user)


@app.route("/account", methods=["GET", "POST"])
def account():
    image_file = url_for('static', filename='image/'+current_user.image_file)
    return render_template("account.html", title="Account", image_file=image_file, user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/post/new', methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Post(title=title, content=note, author=current_user)
            db.session.add(new_note)
            db.session.commit()
            flash('Post added!', category='success')
            return redirect(url_for("home"))
    return render_template("create_post.html", title="New Post" ,user=current_user, legend="New Post")


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post, user=current_user)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post.user_id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully", 'success')
    return redirect(url_for('home'))


@app.route('/user/<string:username>')
def user_posts(username):
    #posts = Post.query.all() -> To query all pages
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template("user_posts.html", posts=posts, user=current_user)


if __name__ == "__main__":
    app.run(debug=True)