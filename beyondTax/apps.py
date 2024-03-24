"""Application config module."""
from django.apps import AppConfig

from beyondTax import container
from beyondTax.settings import INJECTION_MAPPINGS


class BoilerPlateConfig(AppConfig):
    name = "beyondTax"

    def ready(self):
        container.wire(packages=INJECTION_MAPPINGS)
