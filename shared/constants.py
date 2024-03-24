# Guest Message Templates
from beyondTax import settings

GUEST_PAYMENT_REQUEST_TEMPLATE = "guest_payment_reques"
GUEST_ORDER_CONFIRMED_TEMPLATE = "guest_order_confirmed"

# Host Message Templates
HOST_BOOKING_ENQUIRY_CONFIRMATION_TEMPLATE = "host_enquiry_message"
HOST_BOOKING_CONFIRMED_TEMPLATE = "host_order_confirmed"

# Quick Reply Answers
HOST_BOOKING_ENQUIRY_CONFIRMED_STRING = "confirm"


# FrontEnd URLs
FE_PAYMENT_PAGE_URL = settings.FRONTEND_HOST + "/{order_id}/payment/"
FE_PROPERTY_DETAIL_PAGE_URL = settings.FRONTEND_HOST + "/blr/{property_slug}/"
