"""Application config module."""
from django.apps import AppConfig

from boilerPlate import container
from boilerPlate.settings import INJECTION_MAPPINGS


class BoilerPlateConfig(AppConfig):
    name = "boilerPlate"

    def ready(self):
        container.wire(packages=INJECTION_MAPPINGS)
