from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb://localhost:27017/buy-car-mongodb') 
db = client['buyCar']  # название базы данных

@app.route('/')
def ping():
    return 'python working'

from routes.cars import *
from routes.filter import *
