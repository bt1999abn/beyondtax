from decimal import Decimal

from django.db import models

from accounts.models import ServicePages


class ProductProxy(ServicePages):

    class Meta:
        proxy = True
        verbose_name = 'product'
        verbose_name_plural = 'products'

    @property
    def product_name(self):
        return self.service_title

    @property
    def department_name(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, "Unknown Category")

