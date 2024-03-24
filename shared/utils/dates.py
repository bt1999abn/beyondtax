import datetime


def convert_datetime_to_date(date_time, date_format="%d-%m-%Y"):
    return date_time.strftime(date_format)


def convert_datetime_to_time(date_time, date_format="%I:%M %p"):
    return date_time.strftime(date_format)


def convert_time_to_str(time, time_format="%I:%M %p"):
    return time.strftime(time_format)


def convert_datetime_to_string(date_time, date_format="%d-%m-%Y %I:%M %p"):
    """
    Use this method everywhere you want to display time. This format is used throughout the project.
    :param date_time:
    :param date_format:
    :return:
    """
    return date_time.strftime(date_format)


def get_time_difference_in_hours(start_time, end_time):
    # Create datetime objects for each time (a and b)
    dateTimeA = datetime.datetime.combine(datetime.date.today(), start_time)
    dateTimeB = datetime.datetime.combine(datetime.date.today(), end_time)
    # Get the difference between datetimes (as timedelta)
    dateTimeDifference = dateTimeA - dateTimeB
    # Divide difference in seconds by number of seconds in hour (3600)
    dateTimeDifferenceInHours = abs(dateTimeDifference.total_seconds() / 3600)
    # Here we are doing the absolute to remove the minus times.
    return dateTimeDifferenceInHours


def calculate_available_timeslots(start_time, end_time, reserved_timeslots):
    """
    Calculates and gives the available timeslots between the start and end times considering the
    given reserved time slots.
    :param start_time: start time. For ex: 10: 00 AM
    :param end_time: end time. For ex: 8: 00 PM
    :param reserved_timeslots: The list of tuples of (checkin_time, checkout_time) that are already reserved.
    Note: These reserved_timeslots should be in ascending order.
    :return: The list of tuples of (start_time, end_time) that are available between the given start and end times.
    """
    current_start_time = start_time
    available_time_slots = []
    for index, reserved_timeslot in enumerate(reserved_timeslots):
        reserved_start_time, reserved_end_time = reserved_timeslot
        if reserved_start_time > current_start_time:
            current_end_time = reserved_start_time
            # We are showing the times if the time difference is more than 1 hour.
            if get_time_difference_in_hours(current_end_time, current_start_time) >= 1:
                available_time_slots.append(
                    (current_start_time, current_end_time)
                )
        current_start_time = reserved_end_time
    else:
        # This is to append the last remaining time after the last booking time of the day.
        # We are showing the times if the time difference is more than 1 hour.
        if get_time_difference_in_hours(end_time, current_start_time) > 1:
            available_time_slots.append(
                (current_start_time, end_time)
            )
    return available_time_slots
