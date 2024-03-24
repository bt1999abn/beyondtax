from shared.utils import dates as date_utils
from datetime import datetime


class GetObjectDataInSequence:
    def __init__(self, model_instance):
        self.model_instance = model_instance

    def _handle_related_objects(self, attribute):
        attr_list = attribute.split(".")
        value = None
        for index, attr in enumerate(attr_list):
            current_instance = self.model_instance if index == 0 else value
            value = getattr(current_instance, attr)
        return value

    def get_order_data_in_sequence(self, attributes_list: list):
        attribute_values_list = []
        for attribute in attributes_list:
            if type(attribute) != str:
                value = attribute
            elif "." in attribute:
                # Handle related objects data
                value = self._handle_related_objects(attribute)
            else:
                local_attr = attribute
                is_date = attribute.endswith("__date")
                is_time = attribute.endswith("__time")
                if is_date:
                    local_attr = local_attr.replace("__date", "")
                elif is_time:
                    local_attr = local_attr.replace("__time", "")
                value = getattr(self.model_instance, local_attr)
                if is_date:
                    value = date_utils.convert_datetime_to_date(value)
                if is_time:
                    value = date_utils.convert_datetime_to_time(value)
                if isinstance(value, datetime):
                    value = date_utils.convert_datetime_to_string(value)
            attribute_values_list.append(
                str(value)
            )
        return attribute_values_list


def construct_model_field_name(field_label: str):
    """
    This method take a field label which is Changed data and convert to field name which is changed_data
    :param field_label:
    :return:
    """
    return field_label.replace(" ", "_").lower()
