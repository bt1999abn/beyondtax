from django.urls import path
from .views import IncomeTaxProfileApi, ListIncomeTaxReturnsView, ResidentialStatusQuestionsListView, \
    SendPanVerificationOtpApi, VerifyPanOtpApi, ImportIncomeTaxProfileDataApi, TdsOrTcsDeductionUpdateApi, \
    TdsOrTcsDeductionListCreateApi, IncomeFromBettingUpdateApi, IncomeFromBettingListCreateApi, DividendIncomeUpdateApi, \
    DividendIncomeListCreateApi, SalaryIncomeListCreateApi, SalaryIncomeUpdateApi, RentalIncomeListCreateApi, \
    RentalIncomeUpdateApi, CapitalGainsListCreateApi, CapitalGainsUpdateApi, AgricultureIncomeListCreateApi, \
    AgricultureIncomeUpdateApi, BusinessIncomeListCreateApi, BusinessIncomeUpdateApi, ExemptIncomeListCreateApi, \
    ExemptIncomeUpdateApi, InterestIncomeListCreateApi, InterestIncomeUpdateApi, InterestOnItRefundsListCreateApi, \
    InterestOnItRefundsUpdateApi, DeductionsApi, SelfAssesmentAndAdvanceTaxPaidListCreateApi, \
    SelfAssesmentAndAdvanceTaxPaidUpdateApi

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('retrive-incometax-profile/', IncomeTaxProfileApi.as_view(), name='retrive-incometax-profile'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
    path('residential-status-questions/', ResidentialStatusQuestionsListView.as_view(), name='residential-status-questions'),
    path('send-pan-verification-otp/', SendPanVerificationOtpApi.as_view(), name='send_pan_verification_otp'),
    path('verify-pan-otp/', VerifyPanOtpApi.as_view(), name='verify_pan_otp'),
    path('import-tax-profile-data/', ImportIncomeTaxProfileDataApi.as_view(), name='import_tax_profile_data'),
    path('salary-incomes/', SalaryIncomeListCreateApi.as_view(), name='salary-incomes-list-create'),
    path('salary-incomes/<int:pk>/', SalaryIncomeUpdateApi.as_view(), name='salary-incomes-update'),
    path('rental-incomes/', RentalIncomeListCreateApi.as_view(), name='rental-incomes-list-create'),
    path('rental-incomes/<int:pk>/', RentalIncomeUpdateApi.as_view(), name='rental-incomes-update'),
    path('capital-gains/', CapitalGainsListCreateApi.as_view(), name='capital-gains-list-create'),
    path('capital-gains/<int:pk>/', CapitalGainsUpdateApi.as_view(), name='capital-gains-update'),
    path('agriculture-incomes/', AgricultureIncomeListCreateApi.as_view(), name='agriculture-incomes-list-create'),
    path('agriculture-incomes/<int:pk>/', AgricultureIncomeUpdateApi.as_view(), name='agriculture-incomes-update'),
    path('business-incomes/', BusinessIncomeListCreateApi.as_view(), name='business-incomes-list-create'),
    path('business-incomes/<int:pk>/', BusinessIncomeUpdateApi.as_view(), name='business-incomes-update'),
    path('exempt-incomes/', ExemptIncomeListCreateApi.as_view(), name='exempt-incomes-list-create'),
    path('exempt-incomes/<int:pk>/', ExemptIncomeUpdateApi.as_view(), name='exempt-incomes-update'),
    path('interest-incomes/', InterestIncomeListCreateApi.as_view(), name='interest-incomes-list-create'),
    path('interest-incomes/<int:pk>/', InterestIncomeUpdateApi.as_view(), name='interest-incomes-update'),
    path('interest-on-it-refunds/', InterestOnItRefundsListCreateApi.as_view(),
         name='interest-on-it-refunds-list-create'),
    path('interest-on-it-refunds/<int:pk>/', InterestOnItRefundsUpdateApi.as_view(),
         name='interest-on-it-refunds-update'),
    path('dividend-incomes/', DividendIncomeListCreateApi.as_view(), name='dividend-incomes-list-create'),
    path('dividend-incomes/<int:pk>/', DividendIncomeUpdateApi.as_view(), name='dividend-incomes-update'),
    path('income-from-betting/', IncomeFromBettingListCreateApi.as_view(), name='income-from-betting-list-create'),
    path('income-from-betting/<int:pk>/', IncomeFromBettingUpdateApi.as_view(), name='income-from-betting-update'),
    path('tds-or-tcs-deductions/', TdsOrTcsDeductionListCreateApi.as_view(), name='tds-or-tcs-deductions-list-create'),
    path('tds-or-tcs-deductions/<int:pk>/', TdsOrTcsDeductionUpdateApi.as_view(), name='tds-or-tcs-deductions-update'),
    path('self-assessment-and-advance-tax-paid/', SelfAssesmentAndAdvanceTaxPaidListCreateApi.as_view(),
         name='self-assessment-and-advance-tax-paid-list-create'),
    path('self-assessment-and-advance-tax-paid/<int:pk>/', SelfAssesmentAndAdvanceTaxPaidUpdateApi.as_view(),
         name='self-assessment-and-advance-tax-paid-update'),
    path('deductions/', DeductionsApi.as_view(), name='deductions'),
]
