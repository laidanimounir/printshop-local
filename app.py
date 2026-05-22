import os
from flask import Flask
from database import db, init_db
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{config.DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

init_db(app)

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.QR_FOLDER, exist_ok=True)
