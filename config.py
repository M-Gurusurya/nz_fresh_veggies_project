import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/fresh_harvest_veggies'
    SQLALCHEMY_TRACK_MODIFICATIONS = False