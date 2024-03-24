from beyondTax import settings
from shared import utils as shared_utils


def get_guest_order_payment_msg_str(order):
    space_name = order.space.name.title() if order.space else ""
    space_slug = order.space.slug if order.space else ""
    guest_name = order.guest_name.title()
    checkin_datetime = shared_utils.convert_datetime_to_string(order.checkin_datetime)
    gift_for_smile = """
*Gift a smile ⭐️ : ₹5*""" if order.opted_gift_for_smile else ""
    return f"""Dear {guest_name},

To Confirm your booking,
Kindly Pay: *₹{order.order_total}*
UPI ID: coziq@ybl
---------------------------------

Booking Details:
---------------------------------
Space: *{space_name}*
No. of Guest: *{order.number_of_guests}*
Check-in: *{checkin_datetime}*
Duration: *{order.stay_duration} Hours* 


Payment Details:
---------------------------------
Nominal Price: ₹{order.nominal_price}
Taxes: ₹{order.gst_amount}{gift_for_smile}
Total: ₹{order.order_total}
---------------------------------
Space Details : {settings.FRONTEND_HOST}/blr/{space_slug}

*Share payment screenshot with UTR number*

Note: Govt. approved photo ID of all guests required
---------------------------------

Would you like to *confirm your reservation, {guest_name}? 😊✨*
    """


def get_host_confirmed_booking_msg_str(order):
    space_name = order.space.name if order.space else ""
    booking_date = shared_utils.convert_datetime_to_date(order.checkin_datetime.date())
    booking_time = shared_utils.convert_datetime_to_time(order.checkin_datetime.time())
    alcohol_or_hookah = "Yes" if order.has_alcohol or order.has_hookah else "None"
    return f"""*✅BOOKING CONFIRMED 😁*
-----------------------------
💰 Host Earnings : *₹{order.host_share}*
-----------------------------
Guest Name: *{order.guest_name}*
Contact: {order.guest_phone}
-----------------------------
Space: *{space_name}*
No. of Guests: *{order.number_of_guests}*
-----------------------------
Booking Date: *{booking_date}*
Check-In Time: *{booking_time}*
Duration: *{order.stay_duration} Hours*
-----------------------------
Alcohol/Hookah Permit: *{alcohol_or_hookah}*
    """


def get_guest_order_confirmation_msg(order):
    guest_name = order.guest_name.title()
    space_name = order.space.name if order.space else ""
    location_url = order.space.location_url if order.space else ""
    full_address = order.space.full_address if order.space else ""
    host_phone = order.space.host.phone_number if order.space else ""
    checkin_date = shared_utils.convert_datetime_to_date(order.checkin_datetime.date())
    checkin_time = shared_utils.convert_datetime_to_time(order.checkin_datetime.time())
    allowed = """
    Allowed Permit: None"""
    if order.has_alcohol:
        allowed = """
        Allowed Permit: Alcohol"""
    if order.has_hookah:
        allowed = """
        Allowed Permit: Hookah"""
    if order.has_alcohol and order.has_hookah:
        allowed = """
        Allowed Permit: Alcohol/ Hookah"""

    return f"""Dear {guest_name},
*✅ Your Reservation is CONFIRMED! 🤩*

Location Details:
---------------------------------
Google Link: {location_url}

*Address:* {full_address}

*Host Contact:* {host_phone}

Booking Details:
--------------------------------- 
Space: *{space_name}* 
No. of Guest: *{order.number_of_guests}*
Date: *{checkin_date}*
Check-in Time: *{checkin_time}*
Duration: *{order.stay_duration} Hours*{allowed}

NOTE
---------------------------------
1. No PDA or sexual activities allowed
2. No cake smashing/throwing allowed
3. Ensure timely check-in and check-out
4. Any damages/missing items will incur fines
    """


def get_host_order_enquiry_msg(order):
    guest_name = order.guest_name.title()
    space_name = order.space.name if order.space else ""
    checkin_date = shared_utils.convert_datetime_to_date(order.checkin_datetime.date())
    checkin_time = shared_utils.convert_datetime_to_time(order.checkin_datetime.time())
    alcohol_or_hookah = "Yes" if order.has_alcohol or order.has_hookah else "None"
    group_type = order.group_type.name if order.group_type else ""
    return f"""📩 *BOOKING ENQUIRY*
-----------------------------
💰 Host Earning: *₹{order.host_share}*
-----------------------------
Guest Name: *{guest_name}*
Age: *{order.guest_age}*
Profession: *{order.guest_profession}*
-----------------------------
Space: *{space_name}*
No. of Guests: *{order.number_of_guests}*
Group Type: *{group_type}*
-----------------------------
Booking Date: *{checkin_date}*
Check-In Time: *{checkin_time}*
Duration: *{order.stay_duration} Hours*
-----------------------------
Alcohol/Hookah Permit: *{alcohol_or_hookah}*

✅ Reply *CONFIRM* to confirm your availability
🚫 Reply  *PASS* to Skip on this booking.
    """
