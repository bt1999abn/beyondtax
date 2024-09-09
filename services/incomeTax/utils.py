from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from services.incomeTax.models import IncomeTaxReturnYears, InterestIncome, CapitalGains, RentalIncome


class IncomeTaxCurrentYear:

    def get_current_income_tax_return_year(self):
        today = date.today()
        try:
            current_year = IncomeTaxReturnYears.objects.get(start_date__lte=today, end_date__gte=today)
            return current_year
        except IncomeTaxReturnYears.DoesNotExist:
            return None


class IncomeTaxCalculations:

    def round_off_decimal(self, value):
        if isinstance(value, Decimal):
            rounded_value = float(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            return rounded_value
        return value

    def convert_to_json_serializable(self, data):
        """
        Recursively convert Decimal values to float in a dictionary or list.
        """
        if isinstance(data, dict):
            return {key: self.convert_to_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.convert_to_json_serializable(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data

    def calculate_standard_deduction(self, gross_salary, basic_salary, hra_component, annual_rent_paid,
                                     do_you_live_in_these_cities):

        city_based_deduction = basic_salary * Decimal(
            '0.50') if do_you_live_in_these_cities else basic_salary * Decimal('0.40')

        rent_based_deduction = annual_rent_paid - (basic_salary * Decimal('0.10'))

        standard_deduction = min(hra_component, city_based_deduction, rent_based_deduction)

        return standard_deduction

    def calculate_salary_income(self, salary_incomes, base_standard_deduction):
        salary_incomes_data_old = []
        salary_incomes_data_new = []
        total_income_from_salaries_old = Decimal('0')
        total_income_from_salaries_new = Decimal('0')

        for salary_income in salary_incomes:
            regime_specific_standard_deduction_old = self.calculate_standard_deduction(
                salary_income.gross_salary,
                salary_income.basic_salary_component,
                salary_income.hra_component,
                salary_income.annual_rent_paid,
                salary_income.do_you_live_in_these_cities
            )
            total_standard_deduction_old = base_standard_deduction + regime_specific_standard_deduction_old
            total_standard_deduction_new = base_standard_deduction

            total_income_old = salary_income.gross_salary - total_standard_deduction_old
            total_income_new = salary_income.gross_salary - total_standard_deduction_new

            total_income_from_salaries_old += total_income_old
            total_income_from_salaries_new += total_income_new

            salary_incomes_data_old.append({
                "employer_name": salary_income.employer_name,
                "gross_salary": salary_income.gross_salary,
                "standard_deduction": total_standard_deduction_old,
                "total_income": total_income_old
            })

            salary_incomes_data_new.append({
                "employer_name": salary_income.employer_name,
                "gross_salary": salary_income.gross_salary,
                "standard_deduction": total_standard_deduction_new,
                "total_income": total_income_new
            })

        return salary_incomes_data_old, salary_incomes_data_new, total_income_from_salaries_old, total_income_from_salaries_new

    def calculate_rental_income(self, rental_incomes):
        rental_incomes_data = []
        total_rental_income_old = Decimal('0')
        total_rental_income_new = Decimal('0')

        for rental_income in rental_incomes:
            occupancy_status_text = dict(RentalIncome.OCCUPANCY_TYPE_CHOICES).get(rental_income.occupancy_status,
                                                                                  "Unknown")
            interest_on_borrowed_capital = rental_income.standard_deduction + rental_income.interest_on_home_loan_dcp + rental_income.interest_on_home_loan_pc
            total_rental_income = rental_income.annual_rent - interest_on_borrowed_capital
            total_rental_income_old += total_rental_income
            total_rental_income_new += total_rental_income

            rental_income_data = {
                "occupancy_status": occupancy_status_text,
                "annual_rent": rental_income.annual_rent,
                "Interest on Borrowed Capital u/s 24(b)": interest_on_borrowed_capital,
                "total_rental_income": total_rental_income
            }
            if rental_income.occupancy_status == RentalIncome.LetOut:
                rental_income_data["property_tax_paid"] = rental_income.property_tax_paid

            rental_incomes_data.append(rental_income_data)

        return rental_incomes_data, total_rental_income_old, total_rental_income_new

    def calculate_capital_gains(self, capital_gains):
        long_term_capital_gains_112A = Decimal('0')
        long_term_capital_gains_others = Decimal('0')
        short_term_capital_gains = Decimal('0')

        for capital_gain in capital_gains:
            if capital_gain.asset_type == CapitalGains.ListedSharesOrMutualFunds and capital_gain.term_type == CapitalGains.LongTerm:
                long_term_capital_gains_112A += capital_gain.gain_or_loss
            if capital_gain.asset_type == CapitalGains.HouseProperty and capital_gain.term_type == CapitalGains.LongTerm:
                long_term_capital_gains_others += capital_gain.gain_or_loss
            if capital_gain.term_type == CapitalGains.ShortTerm:
                short_term_capital_gains += capital_gain.gain_or_loss

        total_capital_gains_income = long_term_capital_gains_112A + long_term_capital_gains_others + short_term_capital_gains

        return total_capital_gains_income, long_term_capital_gains_112A, long_term_capital_gains_others, short_term_capital_gains

    def calculate_business_income(self, business_incomes):
        business_incomes_data = []
        total_income_from_business = Decimal('0')

        for business_income in business_incomes:
            profit_from_business = business_income.gross_receipt_cheq_neft_rtgs_profit + business_income.gross_receipt_cash_upi_profit
            total_income_from_business += profit_from_business
            business_incomes_data.append({
                "business_income_type": business_income.get_business_income_type_display(),
                "Profit from Business": profit_from_business
            })

        return business_incomes_data, total_income_from_business

    def calculate_deductions(self, deductions, interest_incomes):
        deduction_80c_sum = sum([
            deductions.life_insurance,
            deductions.provident_fund,
            deductions.elss_mutual_fund,
            deductions.home_loan_repayment,
            deductions.tution_fees,
            deductions.stamp_duty_paid,
            deductions.others
        ]) if deductions else 0
        if deduction_80c_sum > Decimal('150000'):
            deduction_80c_sum = Decimal('150000')

        nps_contribution_sum = (
                    deductions.contribution_by_self + deductions.contribution_by_employeer) if deductions else 0

        medical_premium_sum = sum([
            deductions.medical_insurance_self,
            deductions.medical_preventive_health_checkup_self,
            deductions.medical_expenditure_self,
            deductions.medical_insurance_parents,
            deductions.medical_preventive_health_checkup_parents,
            deductions.medical_expenditure_parents
        ]) if deductions else 0
        if deductions and deductions.senior_citizen_parents:
            if medical_premium_sum > Decimal('125000'):
                medical_premium_sum = Decimal('125000')
        else:
            if medical_premium_sum > Decimal('100000'):
                medical_premium_sum = Decimal('100000')

        interest_on_savings_sum = sum(
            [income.interest_amount for income in interest_incomes if
             income.interest_income_type == InterestIncome.SavingsBankAccount]
        )
        if interest_on_savings_sum > Decimal('10000'):
            interest_on_savings_sum = Decimal('10000')

        return deduction_80c_sum, nps_contribution_sum, medical_premium_sum, interest_on_savings_sum

    def calculate_tds_advance_tax(self, tds_deductions, self_assessment_advance_tax, start_date, end_date):
        total_tds_or_tcs = sum(tds.tds_or_tcs_amount for tds in tds_deductions)
        total_self_assessment_tax = Decimal('0')
        total_advance_tax = Decimal('0')

        for tax_record in self_assessment_advance_tax:
            if start_date and end_date:
                if start_date <= tax_record.date <= end_date:
                    total_advance_tax += tax_record.amount
                else:
                    total_self_assessment_tax += tax_record.amount

        return total_tds_or_tcs, total_self_assessment_tax, total_advance_tax

    def calculate_gross_total_income(self, total_income_from_salaries, total_rental_income, total_income_from_business,
                                     total_capital_gains_income, total_interest_income, total_dividend_income, total_winnings_income, total_combined_exempt_income):
        return (
            total_income_from_salaries + total_rental_income + total_income_from_business +
            total_capital_gains_income + total_interest_income + total_dividend_income + total_winnings_income +
            total_combined_exempt_income
        )

    def calculate_tax_liability_old_regime(self, total_income):
        tax = Decimal(0)
        if total_income <= 250000:
            return tax
        elif total_income <= 500000:
            tax += (Decimal(total_income) - Decimal(250000)) * Decimal('0.05')
        elif total_income <= 1000000:
            tax += (Decimal(500000) - Decimal(250000)) * Decimal('0.05')
            tax += (Decimal(total_income) - Decimal(500000)) * Decimal('0.20')
        else:
            tax += (Decimal(500000) - Decimal(250000)) * Decimal('0.05')
            tax += (Decimal(1000000) - Decimal(500000)) * Decimal('0.20')
            tax += (Decimal(total_income) - Decimal(1000000)) * Decimal('0.30')

        return tax

    def calculate_tax_liability_new_regime(self, total_income):
        tax = Decimal(0)
        if total_income <= 300000:
            return tax
        elif total_income <= 600000:
            tax += (Decimal(total_income) - Decimal(300000)) * Decimal('0.05')
        elif total_income <= 900000:
            tax += (Decimal(600000) - Decimal(300000)) * Decimal('0.05')
            tax += (Decimal(total_income) - Decimal(600000)) * Decimal('0.10')
        elif total_income <= 1200000:
            tax += (Decimal(600000) - Decimal(300000)) * Decimal('0.05')
            tax += (Decimal(900000) - Decimal(600000)) * Decimal('0.10')
            tax += (Decimal(total_income) - Decimal(900000)) * Decimal('0.15')
        elif total_income <= 1500000:
            tax += (Decimal(600000) - Decimal(300000)) * Decimal('0.05')
            tax += (Decimal(900000) - Decimal(600000)) * Decimal('0.10')
            tax += (Decimal(1200000) - Decimal(900000)) * Decimal('0.15')
            tax += (Decimal(total_income) - Decimal(1200000)) * Decimal('0.20')
        else:
            tax += (Decimal(600000) - Decimal(300000)) * Decimal('0.05')
            tax += (Decimal(900000) - Decimal(600000)) * Decimal('0.10')
            tax += (Decimal(1200000) - Decimal(900000)) * Decimal('0.15')
            tax += (Decimal(1500000) - Decimal(1200000)) * Decimal('0.20')
            tax += (Decimal(total_income) - Decimal(1500000)) * Decimal('0.30')

        return tax

    def calculate_tax_rebate_old_regime(self, total_income, tax_liability):
        if total_income <= 500000:
            max_rebate = Decimal(12500)
            return min(max_rebate, tax_liability)
        return Decimal(0)

    def calculate_tax_rebate_new_regime(self, total_income, tax_liability):
        if total_income <= 700000:
            max_rebate = Decimal(25000)
            return min(max_rebate, tax_liability)
        return Decimal(0)

    def calculate_surcharge(self, total_income, tax_liability, regime):
        surcharge = Decimal(0)

        if total_income <= 5000000:
            return surcharge
        elif total_income <= 10000000:
            surcharge = (total_income - Decimal(5000000)) * Decimal('0.10')
        elif total_income <= 20000000:
            surcharge = (total_income - Decimal(10000000)) * Decimal('0.15')
        elif total_income <= 50000000:
            surcharge = (total_income - Decimal(20000000)) * Decimal('0.25')
        else:
            if regime == "old":
                surcharge = (total_income - Decimal(50000000)) * Decimal('0.37')
            elif regime == "new":
                surcharge = (total_income - Decimal(50000000)) * Decimal('0.25')

        return surcharge

    def calculate_cess(self, tax_liability, surcharge, tax_rebate):
        return (tax_liability + surcharge - tax_rebate) * Decimal('0.04')

    def calculate_interest_234A(self, balance_tax_to_be_paid, filing_date, due_date):
        if filing_date <= due_date:
            return Decimal('0')
        # Calculate months of delay
        months_of_delay = (filing_date.year - due_date.year) * 12 + (filing_date.month - due_date.month)
        return balance_tax_to_be_paid * Decimal('0.01') * months_of_delay

    def calculate_interest_234B(self, balance_tax_to_be_paid, total_advance_tax, net_tax_payable):
        if total_advance_tax >= net_tax_payable * Decimal('0.90'):
            return Decimal('0')
        months = 9
        return balance_tax_to_be_paid * Decimal('0.01') * months

    def calculate_interest_234C(self, balance_tax_to_be_paid, total_advance_tax, net_tax_payable):

        interest_234C = Decimal('0')
        required_installments = [Decimal('0.15'), Decimal('0.45'), Decimal('0.75'), Decimal('1.00')]
        installment_dates = ['June 15', 'September 15', 'December 15', 'March 15']

        for i, percent in enumerate(required_installments):
            required_tax = net_tax_payable * percent
            if total_advance_tax < required_tax:
                shortfall = required_tax - total_advance_tax
                # Calculate the months of delay for each installment
                interest_234C += shortfall * Decimal('0.01') * 3  # Assuming 3 months per installment

        return interest_234C

    def calculate_penalty_us_234F(self, total_income, filing_date, due_date):
        """
        Calculate penalty u/s 234F based on filing date, due date, and total income.
        """

        # Ensure that filing_date and due_date are of type datetime.date or datetime.datetime
        if isinstance(filing_date, int):
            # If filing_date is a timestamp integer, convert it to a date
            filing_date = datetime.fromtimestamp(filing_date).date()
        elif isinstance(filing_date, datetime):
            filing_date = filing_date.date()  # Convert datetime to date if necessary

        if isinstance(due_date, int):
            # If due_date is a timestamp integer, convert it to a date
            due_date = datetime.fromtimestamp(due_date).date()
        elif isinstance(due_date, datetime):
            due_date = due_date.date()  # Convert datetime to date if necessary

        # Define penalty amounts
        penalty = 0

        # Check if filing is delayed
        if filing_date > due_date:
            if total_income <= 500000:
                # If income is <= 5,00,000, penalty is restricted to ₹1,000
                penalty = 1000
            elif filing_date <= datetime(filing_date.year, 12, 31).date():
                penalty = 5000
            else:
                penalty = 10000

        return penalty