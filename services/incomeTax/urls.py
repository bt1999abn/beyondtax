from django.urls import path
from .views import IncomeTaxProfileApi, ListIncomeTaxReturnsView, ResidentialStatusQuestionsListView, \
    SendPanVerificationOtpApi, VerifyPanOtpApi, ImportIncomeTaxProfileDataApi, \
    SalaryIncomeListCreateApi, SalaryIncomeUpdateApi, RentalIncomeListCreateApi, \
    RentalIncomeUpdateApi, CapitalGainsListCreateApi, CapitalGainsUpdateApi, \
    BusinessIncomeListCreateApi, BusinessIncomeUpdateApi, DeductionsApi, AgricultureAndExemptIncomeApi, OtherIncomesApi, \
    TaxPaidApi, TotalIncomeGetAPIView, TotalSummaryGetAPI

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('retrive-incometax-profile/', IncomeTaxProfileApi.as_view(), name='retrive-incometax-profile'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
    path('residential-status-questions/', ResidentialStatusQuestionsListView.as_view(), name='residential-status-questions'),
    path('send-pan-verification-otp/', SendPanVerificationOtpApi.as_view(), name='send_pan_verification_otp'),
    path('verify-pan-otp/', VerifyPanOtpApi.as_view(), name='verify_pan_otp'),
    path('import-tax-profile-data/', ImportIncomeTaxProfileDataApi.as_view(), name='import_tax_profile_data'),
    path('salary-incomes/<int:income_tax_return_id>/', SalaryIncomeListCreateApi.as_view(),
         name='salary-income-list-create'),
    path('salary-incomes/<int:income_tax_return_id>/update/', SalaryIncomeUpdateApi.as_view(),
         name='salary-income-update'),
    path('rental-incomes/<int:income_tax_return_id>/', RentalIncomeListCreateApi.as_view(),
         name='rental-income-list-create'),
    path('rental-incomes/<int:income_tax_return_id>/update/', RentalIncomeUpdateApi.as_view(),
         name='rental-income-update'),
    path('capital-gains/<int:income_tax_return_id>/', CapitalGainsListCreateApi.as_view(),
         name='capital-gains-list-create'),
    path('capital-gains/<int:income_tax_return_id>/update/', CapitalGainsUpdateApi.as_view(),
         name='capital-gains-update'),
    path('business-incomes/<int:income_tax_return_id>/', BusinessIncomeListCreateApi.as_view(),
         name='business-income-list-create'),
    path('business-incomes/<int:income_tax_return_id>/update/', BusinessIncomeUpdateApi.as_view(),
         name='business-income-update'),
    path('agriculture-and-exempt-incomes/<int:income_tax_return_id>/', AgricultureAndExemptIncomeApi.as_view(),
         name='agriculture-and-exempt-incomes'),
    path('other-incomes/<int:income_tax_return_id>/', OtherIncomesApi.as_view(), name='other-incomes'),
    path('tax-paid/<int:income_tax_return_id>/', TaxPaidApi.as_view(), name='tax-paid'),
    path('deductions/<int:income_tax_return_id>/', DeductionsApi.as_view(), name='deductions'),
    path('total-income/<int:income_tax_return_id>/', TotalIncomeGetAPIView.as_view(), name='total-income-get-api'),
    path('total-tax-summary/<int:income_tax_return_id>/', TotalSummaryGetAPI.as_view(), name='total-tax-summary'),
]
