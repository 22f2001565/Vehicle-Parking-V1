from flask import current_app as app
from flask import request, redirect, render_template, url_for
from models.models import *
from datetime import datetime

@app.route("/admin_dashboard")
def admin_dashboard():
    parking_lots= ParkingLot.query.all()
    lots_data= []
    for lot in parking_lots:
        spots= ParkingSpot.query.filter_by(lot_id=lot.id).all()
        occupied= sum(1 for spot in spots if spot.status=='O')
        lots_data.append({
            'lot': lot,
            'spots': spots,
            'occupied': occupied,
            "total_spots": len(spots)
        })
    return render_template('admin_dash.html', lots=lots_data)


@app.route("/add_lot", methods= ["GET", "POST"])
def add_lot():
    if request.method== "POST":
        prime_location_name= request.form["location"]
        address= request.form["address"]
        pincode= request.form["pincode"]
        price= request.form["price"]
        number_of_spots= request.form["spots"]

        lot= ParkingLot(
            prime_location_name= prime_location_name,
            price= price,
            address= address,
            pin_code= pincode,
            number_of_spots= number_of_spots
        )
        db.session.add(lot)
        db.session.commit()

        for i in range(int(number_of_spots)):
            spot= ParkingSpot(lot_id= lot.id, status="A")
            db.session.add(spot)
        db.session.commit()

        return redirect("/admin_dashboard")
    return render_template("add_lot.html")


@app.route("/edit_lot/<int:lot_id>", methods=["GET", "POST"])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == "POST":
        lot.prime_location_name = request.form["location"] 
        lot.address = request.form["address"]
        lot.pin_code = request.form["pincode"]
        lot.price = float(request.form["price"])

        new_spot_count = int(request.form["spots"])
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        current_count = len(current_spots)

        lot.number_of_spots = new_spot_count

        if new_spot_count > current_count:
            for _ in range(new_spot_count - current_count):
                new_spot = ParkingSpot(lot_id=lot.id, status='A')
                db.session.add(new_spot)
        elif new_spot_count < current_count:
            removable = [spot for spot in current_spots if spot.status == 'A']
            to_remove = removable[:(current_count - new_spot_count)]
            for spot in to_remove:
                db.session.delete(spot)

        db.session.commit()
        return redirect("/admin_dashboard")

    return render_template("edit_lot.html", lot=lot)


@app.route("/delete_lot/<int:lot_id>")
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

    for spot in spots:
        if spot.status == "O":
            return render_template("delete_lot.html", message="Cannot delete: a spot is currently occupied.")

        has_active_reservation = Reservation.query.filter(
            Reservation.spot_id == spot.id,
            Reservation.leaving_timestamp > datetime.utcnow()
        ).first()

        if has_active_reservation:
            return render_template("delete_lot.html", message="Cannot delete: a spot has an active or upcoming reservation.")

    for spot in spots:
        db.session.delete(spot)
    db.session.delete(lot)
    db.session.commit()

    return redirect("/admin_dashboard")


@app.route('/lot_detail/<int:lot_id>')
def lot_detail(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return "Lot not found", 404

    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    occupied_count = sum(1 for spot in spots if spot.status == 'O')
    total_spots = len(spots)

    return render_template(
        'lot_details.html',
        lot=lot,
        spots=spots,
        occupied_count=occupied_count,
        total_spots=total_spots
    )


@app.route("/view_spot/<int:spot_id>", methods=["GET", "POST"])
def view_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    reservation = None

    if spot.status == "O":
        reservation = Reservation.query.filter_by(spot_id=spot_id).first()

    if request.method == "POST":
        if 'delete' in request.form:
            if spot.status == "O":
                print("Cannot delete an occupied parking spot.", "danger")
                return redirect(url_for('view_spot', spot_id=spot_id))

            db.session.delete(spot)
            db.session.commit()
            print("Parking spot deleted successfully.", "success")
            return redirect(url_for('admin_dashboard')) 

    return render_template("view_spot_details.html", spot=spot, reservation=reservation)


@app.route('/parking_detail/<int:spot_id>')
def parking_detail(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status != 'O':
        return redirect(url_for('view_spot', spot_id=spot_id))

    reservation = Reservation.query.filter_by(spot_id=spot_id).first()

    if not reservation:
        return redirect(url_for('view_spot', spot_id=spot_id))

    return render_template('parking_detail.html', reservation=reservation, spot=spot)


@app.route("/delete_spot/<int:spot_id>", methods=["POST"])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status == "O":
        return render_template("del_spot.html", spot=spot)

    lot_id = spot.lot_id  
    db.session.delete(spot)
    db.session.commit()
    return redirect(url_for('lot_detail', lot_id=lot_id))


@app.route("/user_details", methods=["GET"])
def reg_users():
    users = User.query.filter(User.id > 1).all()
    return render_template('user_details.html', users=users)


@app.route('/admin_search', methods=['GET'])
def admin_search():
    query = request.args.get('query', '').strip()

    if query:
        lots_by_location = ParkingLot.query.filter(ParkingLot.prime_location_name.ilike(f"%{query}%")).all()
        lots_by_address = ParkingLot.query.filter(ParkingLot.address.ilike(f"%{query}%")).all()
        lots_by_pincode = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f"%{query}%")).all()

        lots = {lot.id: lot for lot in (lots_by_location + lots_by_address + lots_by_pincode)}.values()
    else:
        lots = ParkingLot.query.all()

    return render_template(
        'admin_search.html',
        lots=lots,
        search_query=query
    )


@app.route("/view_users")
def view_users():
    user_id = request.args.get('user_id', None)
    if user_id:
        user = User.query.get(user_id)

        if user:
            reservation = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).first()

            if reservation:
                return render_template("parking_detail.html", reservation=reservation, user=user)
            else:
                return "No active reservation for this user", 404
        else:
            return "User not found", 404
    else:
        return "User ID is required", 400


@app.route("/admin_summary")
def redirect_to_table_summary():
    return redirect('/admin/summary/table')


@app.route("/admin/summary/table")
def admin_summary_table():
    reservations = Reservation.query.all()
    return render_template('admin_sum_t.html', reservations=reservations)


@app.route("/admin/summary/chart")
def admin_summary_chart():
    lots = ParkingLot.query.all()
    chart_data = []
    for lot in lots:
        total_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="O").count()
        revenue = (
            Reservation.query
            .join(ParkingSpot)
            .filter(ParkingSpot.lot_id == lot.id)
            .with_entities(db.func.sum(Reservation.parking_cost))
            .scalar() or 0
        )

        chart_data.append({
            "lot": lot.prime_location_name,
            "occupied": occupied_spots,
            "available": total_spots - occupied_spots,
            "revenue": revenue
        })

    return render_template("admin_sum_c.html", chart_data=chart_data)