from flask import current_app as app
from flask import request, redirect, render_template, url_for
from datetime import datetime
from models.models import *
import math
from sqlalchemy import or_

@app.route('/user_dashboard/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    reservations = Reservation.query.filter_by(user_id=user.id).filter(Reservation.leaving_timestamp == None).all()
    released_reservations = Reservation.query.filter_by(user_id=user.id).filter(Reservation.leaving_timestamp != None).all()
    parking_lots = ParkingLot.query.all()
    return render_template(
        'user_dash.html',
        user=user,
        reservations=reservations,
        released_reservations=released_reservations,
        parking_lots=parking_lots
    )


@app.route('/user_search/<int:user_id>', methods=['GET'])
def user_search(user_id):
    user = User.query.get_or_404(user_id)
    search = request.args.get('query', '').strip()

    if search:
        by_location = ParkingLot.query.filter(ParkingLot.prime_location_name.ilike(f"%{search}%")).all()
        by_address = ParkingLot.query.filter(ParkingLot.address.ilike(f"%{search}%")).all()
        by_pincode = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f"%{search}%")).all()

        combined = {lot.id: lot for lot in (by_location + by_address + by_pincode)}
        parking_lots = list(combined.values())
    else:
        parking_lots = ParkingLot.query.all()

    return render_template(
        'user_search.html',
        user=user,
        parking_lots=parking_lots
    )


@app.route('/book_slot/<int:lot_id>/<int:user_id>', methods=['GET', 'POST'])
def book_slot(lot_id, user_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    user = User.query.get_or_404(user_id)
    vehicle_no = request.form.get('vehicle_no')

    existing_booking = Reservation.query.join(ParkingSpot).filter(
        Reservation.user_id == user.id,
        ParkingSpot.lot_id == lot.id,
        Reservation.leaving_timestamp == None 
    ).first()

    if existing_booking:
        return render_template("slot_warn.html", lot=lot, user=user)  

    available_spot = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').first()
    
    if not available_spot:
        return render_template("no_spots.html", lot=lot, user=user)
    
    if request.method == 'POST':
        if available_spot:
            reservation = Reservation(
                spot_id=available_spot.id,
                user_id=user.id,
                vehicle_num=vehicle_no,
                parking_timestamp=datetime.now(),
                parking_cost=lot.price 
            )

            available_spot.status = 'O' 
            lot.number_of_spots -= 1 
            db.session.add(reservation)
            db.session.commit()  

            return redirect(url_for('user_dashboard', user_id=user.id))
        else:
            return render_template("no_spots.html", lot=lot, user=user)
    return render_template("book_slot.html", lot=lot, user=user, spot=available_spot)


def calculate_parking_cost(parking_timestamp, leaving_timestamp, price_per_hour):
    duration = leaving_timestamp - parking_timestamp
    total_minutes = duration.total_seconds() / 60
    total_hours = total_minutes / 60
    chargeable_hours = math.ceil(total_hours)  
    return round(chargeable_hours * price_per_hour, 2)


@app.route('/release_parking/<int:reservation_id>', methods=['GET', 'POST'])
def release_parking(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    spot = ParkingSpot.query.get_or_404(reservation.spot_id)
    user = User.query.get_or_404(reservation.user_id)
    lot = ParkingLot.query.get_or_404(spot.lot_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'cancel':
            return redirect(url_for('user_dashboard', user_id=user.id))

        elif action == 'release':
            now = datetime.now()
            reservation.leaving_timestamp = now
            reservation.parking_cost = calculate_parking_cost(reservation.parking_timestamp, now, lot.price)
            reservation.status = 'released'
            spot.status = 'A'
            lot.number_of_spots += 1

            db.session.commit()
            return redirect(url_for('user_dashboard', user_id=user.id))

    now = datetime.now()
    preview_cost = calculate_parking_cost(reservation.parking_timestamp, now, lot.price)

    return render_template(
        'release_spot.html',
        reservation=reservation,
        spot=spot,
        user=user,
        lot=lot,
        preview_time=now,
        preview_cost=preview_cost
    )


@app.route("/user_summary/<int:user_id>")
def user_summary(user_id):
    user = User.query.get_or_404(user_id)
    all_reservations = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.parking_timestamp.desc()).all()

    def format_duration(minutes):
        if minutes is None:
            return 'In Progress'
        if minutes < 60:
            return f"{int(minutes)} min"
        hours = int(minutes) // 60
        mins = int(minutes) % 60
        return f"{hours} hr{'s' if hours > 1 else ''}" + (f" {mins} min" if mins else "")

    for res in all_reservations:
        duration_minutes = (
            (res.leaving_timestamp - res.parking_timestamp).total_seconds() // 60
            if res.leaving_timestamp else None
        )
        res.duration = format_duration(duration_minutes)

    return render_template(
        "user_sum.html",
        user=user,
        reservations=all_reservations
    )


@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form['email']
        user.full_name = request.form['full_name']
        user.address = request.form['address']
        user.pincode = request.form['pincode']

        try:
            db.session.commit()
            return redirect(url_for('user_dashboard', user_id=user.id))
        except:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error="Update failed. Try again.")

    return render_template('edit_profile.html', user=user)