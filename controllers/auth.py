from flask import current_app as app
from flask import request, redirect, render_template
from models.models import *

@app.route("/")
def home():
    return redirect("/login")

@app.route("/registration", methods=["GET", "POST"])
def register():
    if request.method== "POST":
        email= request.form.get("email")
        password= request.form.get("password")
        fullname= request.form.get("fullname")
        address= request.form.get("address")
        pincode= request.form.get("pincode")
        existing_user= User.query.filter_by(email=email).first()
        if existing_user:
            return "User already Exists"
        else:
            new_user= User(email=email, password=password, full_name=fullname, address=address, pincode=pincode)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
    return render_template("registration.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method== "POST":
        email= request.form.get("email")
        password= request.form.get("password")
        this_user= User.query.filter_by(email=email).first()
        if this_user:
            if this_user.password== password:
                if this_user.type== "admin":
                    return redirect("/admin_dashboard")
                else:
                    return redirect(f"/user_dashboard/{this_user.id}")
            else:
                return "Password is Incorrect"
        else:
            return "User does not Exist"
    return render_template("login.html")