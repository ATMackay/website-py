import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import  DeclarativeBase


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

with app.app_context():
    db.create_all()
