from datetime import date
from services.incomeTax.models import IncomeTaxReturnYears


class IncomeTaxCurrentYear:

    def get_current_income_tax_return_year(self):
        today = date.today()
        try:
            current_year = IncomeTaxReturnYears.objects.get(start_date__lte=today, end_date__gte=today)
            return current_year
        except IncomeTaxReturnYears.DoesNotExist:
            return None