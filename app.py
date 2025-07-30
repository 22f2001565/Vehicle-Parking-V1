from flask import Flask
from models.models import *

app= None

def create_app():
    app= Flask(__name__)
    app.debug= True
    app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///instance/parking_app.db"
    db.init_app(app)
    app.app_context().push()

    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@gmail.com").first():
            admin = User(
                email="admin@gmail.com",
                password="admin123",
                full_name="Admin",
                address="Admin",
                pincode="000000",
                type="admin"
            )
            db.session.add(admin)
            db.session.commit()
        
    return app

app= create_app()
from controllers.auth import *
from controllers.admin import *
from controllers.users import *

if __name__== "__main__":
    app.run(debug=True)