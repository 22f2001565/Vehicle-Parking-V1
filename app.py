from flask import Flask
from models.models import *

app= None

def create_app():
    app= Flask(__name__)
    app.debug= True
    app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///parking_app.db"
    db.init_app(app)
    app.app_context().push()

    with app.app_context():
        db.create_all()
        
    return app

app= create_app()
from controllers.auth import *

if __name__== "__main__":
    app.run(debug=True)