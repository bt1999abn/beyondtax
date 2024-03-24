import datetime

from django.contrib import admin
from django.contrib.admin.utils import lookup_spawns_duplicates, construct_change_message
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import ForeignKey
from django.db.models.constants import LOOKUP_SEP
from django.utils.safestring import mark_safe
from django.utils.text import smart_split, unescape_string_literal

from boilerPlate import settings
from shared.libs.hashing import AlphaId
from shared import utils as shared_utils


class BaseModelAdmin(admin.ModelAdmin):
    def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        # Apply keyword searches.
        def construct_search(field_name):
            if settings.ENCODED_ID_ATTR in field_name:
                field_name = field_name.replace(settings.ENCODED_ID_ATTR, "id")
            if field_name.startswith("^"):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith("="):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith("@"):
                return "%s__search" % field_name[1:]
            # Use field_name if it includes a lookup.
            opts = queryset.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == "pk":
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                    if isinstance(field, ForeignKey) and "_id" in path_part:
                        return field_name
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        return field_name
                else:
                    prev_field = field
                    if hasattr(field, "path_infos"):
                        # Update opts to follow the relation.
                        opts = field.path_infos[-1].to_opts
            # Otherwise, use the field with icontains.
            return "%s__icontains" % field_name

        may_have_duplicates = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = [
                construct_search(str(search_field)) for search_field in search_fields
            ]
            term_queries = []
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                or_queries = models.Q.create(
                    [
                        (orm_lookup, AlphaId.decode(bit) if "id" in orm_lookup and not str(bit).isnumeric() else bit)
                        for orm_lookup in orm_lookups
                    ],
                    connector=models.Q.OR,
                )
                term_queries.append(or_queries)
            queryset = queryset.filter(models.Q.create(term_queries))
            may_have_duplicates |= any(
                lookup_spawns_duplicates(self.opts, search_spec)
                for search_spec in orm_lookups
            )
        return queryset, may_have_duplicates

    def get_colored_cell_html(self, value, warning=False):
        css_class = "warning" if warning else ""
        return mark_safe(f'<span class="{css_class}">{value}</span>')

    def construct_change_message(self, request, form, formsets, add=False):
        """
        Construct a JSON structure describing changes from a changed object.
        """
        default_message_dict = construct_change_message(form, formsets, add)
        if form.changed_data and "changed" in default_message_dict[0]:
            default_message_fields = default_message_dict[0]["changed"]["fields"]
            initial_data = form.initial
            new_data = form.cleaned_data
            new_messages_list = []
            for message_field in default_message_fields:
                model_field_name = shared_utils.construct_model_field_name(field_label=message_field)
                old_field_data = initial_data[model_field_name]
                new_field_data = new_data[model_field_name]
                if isinstance(old_field_data, datetime.datetime):
                    old_field_data = shared_utils.convert_datetime_to_string(old_field_data)
                    new_field_data = shared_utils.convert_datetime_to_string(new_field_data)
                new_messages_list.append(f"{message_field} from {old_field_data} to {new_field_data}")
            default_message_dict[0]["changed"]["fields"] = new_messages_list
        return default_message_dict
