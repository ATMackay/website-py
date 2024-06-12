from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import logging
# Import modules and classes from local project 
from app import app, db
from models import User, BlogPost, Comment
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import os
from smtp import SMTPServer


'''
Make sure the required packages are installed: 

Execute 'make install-dependencies && make env'. 

Alternatively if you wish to install dependencies manually...

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

ADMIN_EMAIL = os.environ.get("ROOT_USER_EMAIL")
MAIL_ADDRESS = os.environ.get("EMAIL_KEY")
MAIL_APP_PW = os.environ.get("PASSWORD_KEY")

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.email != ADMIN_EMAIL:
            logging.warning(
                "User %s (EMAIL='%s') tried to access admin_only endpoint (ROOT_EMAIL='%s')",
                current_user.id, current_user.email, ADMIN_EMAIL
            )
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function



# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        logging.info("New user: [%s, %s]", form.name.data, form.email.data)
        return redirect(url_for("landing_page"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Email/password combination incorrect, please try again.')
            return redirect(url_for('login'))
        login_user(user)
        logging.info("User logged in: [%s, %s]", user.name, user.email)
        return redirect(url_for('landing_page'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing_page'))

@app.route('/')
def landing_page():
    return render_template("landing.html", current_user=current_user)

@app.route('/blog')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    try:
        requested_post = db.get_or_404(BlogPost, post_id)
    except Exception as e:
        logging.error("Error loading post '%d': %s", post_id, e)
        return None
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    """Creates a new post for the server to store.

    Returns:
        None
    """
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("landing_page"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    try:
        post = db.get_or_404(BlogPost, post_id)
    except Exception as e:
        logging.error("Error loading post '%d': %s", post_id, e)
        return None
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    try:
        post_to_delete = db.get_or_404(BlogPost, post_id)
    except Exception as e:
        logging.error("Error loading post '%d': %s", post_id, e)
        return None
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('landing_page'))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        email = data["email"]
        phone_number = data["phone"]
        message = data["message"]
        send_email(name=name, email=email, phone=phone_number, message=message)
        logging.info("Contact email sent, sender=%s", email)
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)

def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    server = SMTPServer("Outlook", MAIL_ADDRESS, MAIL_APP_PW)
    server.connect()
    server.send(MAIL_ADDRESS, MAIL_ADDRESS, email_message)
    server.close()


if __name__ == "__main__":
    app.run(debug=os.environ.get('DEBUG_MODE', False), port=5001) # set debug=False for local development
