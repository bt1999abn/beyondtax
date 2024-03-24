HOST_BOOKING_ENQUIRY_CONFIRMATION_TEMPLATE = """
📩 BOOKING ENQUIRY
-----------------------------
💰 Host Earning: {{1}}
-----------------------------
Guest Name: {{2}}
Age: {{3}}
Profession: {{4}}
-----------------------------
Space: {{5}}
No. of Guests: {{6}}
Group Type: {{7}}
-----------------------------
Booking Date: {{8}}
Check-In Time: {{9}}
Duration: {{10}}
-----------------------------
Alcohol/Hookah Permit: {{11}}

✅ Reply CONFIRM to confirm your availability
🚫 Reply  PASS to Skip on this booking.
"""

GUEST_PAYMENT_REQUEST_TEMPLATE = """
Dear {{1}},

To Confirm your booking,
Kindly Pay: ₹{{2}}
Link to Pay: {{3}}
---------------------------------

Booking Details:
---------------------------------
Space: {{4}}
No. of Guest: {{5}}
Check-in: {{6}}
Duration: {{7}} Hours

Payment Details:
---------------------------------
Nominal Price: ₹{{8}}
Taxes: ₹{{9}}
Total: ₹{{10}}
---------------------------------
Space Details : {{11}}

Note: Govt. approved photo ID of all guests required
---------------------------------

Would you like to confirm your reservation, {{1}}? 😊✨
"""

GUEST_ORDER_CONFIRMED_TEMPLATE = """
Dear {{1}},
✅ Your Reservation is CONFIRMED! 🤩

Location Details:
---------------------------------
Google Link: {{2}}

Address: {{3}}

Host Contact: {{4}}

Booking Details:
--------------------------------- 
Space: {{5}} 
No. of Guest: {{6}}
Date: {{7}}
Check-in Time: {{8}}
Duration: {{9}} Hours

NOTE
---------------------------------
1. No PDA or sexual activities allowed
2. No cake smashing/throwing allowed
3. Ensure timely check-in and check-out
4. Any damages/missing items will incur fines
"""


HOST_BOOKING_CONFIRMED_TEMPLATE = """
✅BOOKING CONFIRMED 😁
-----------------------------
💰 Host Earnings : ₹{{1}}
-----------------------------
Guest Name: {{2}}
Contact: {{3}}
-----------------------------
Space: {{4}}
No. of Guests: {{5}}
-----------------------------
Booking Date: {{6}}
Check-In Time: {{7}}
Duration: {{8}} Hours
-----------------------------
Alcohol/Hookah Permit: {{9}}
"""