from django.urls import path
from .views import ListIncomeTaxReturnsView, ResidentialStatusQuestionsListView, \
    SendPanVerificationOtpApi, VerifyPanOtpApi, ImportIncomeTaxProfileDataApi, \
    SalaryIncomeListCreateApi, SalaryIncomeUpdateApi, RentalIncomeListCreateApi, \
    RentalIncomeUpdateApi, CapitalGainsListCreateApi, CapitalGainsUpdateApi, \
    BusinessIncomeListCreateApi, BusinessIncomeUpdateApi, DeductionsApi, AgricultureAndExemptIncomeApi, OtherIncomesApi, \
    TaxPaidApi, TotalIncomeGetAPIView, TotalSummaryGetAPI, TdsPdfUploadApi, ChallanUploadApi, \
    AISPdfUploadApi, IncomeTaxReturnYearListAPIView, Download26ASAPIView, \
    DownloadAISAPIView, ReportsPageAPIView, DownloadTISAPIView, TaxRefundAPIView, ComputationsOldRegimeApi, \
    ComputationsNewRegimeApi, SummaryPageApi, ComputationsCreateApi, IncomeTaxPdfView, \
    IncometaxComputationsOldPdfView, IncometaxComputationsNewPdfView, IncomeTaxProfileApi

urlpatterns = [
    path('create-incometax-profile/', IncomeTaxProfileApi.as_view(), name='create-incometax-profile'),
    path('update-incometax-profile/', IncomeTaxProfileApi.as_view(), name='update-incometax-profile'),
    path('retrive-incometax-profile/', IncomeTaxProfileApi.as_view(), name='retrive-incometax-profile'),
    path('income-tax-returns/', ListIncomeTaxReturnsView.as_view(), name='user-income-tax-returns'),
    path('residential-status-questions/', ResidentialStatusQuestionsListView.as_view(), name='residential-status-questions'),
    path('send-pan-verification-otp/', SendPanVerificationOtpApi.as_view(), name='send_pan_verification_otp'),
    path('verify-pan-otp/', VerifyPanOtpApi.as_view(), name='verify_pan_otp'),
    path('import-tax-profile-data/', ImportIncomeTaxProfileDataApi.as_view(), name='import_tax_profile_data'),
    path('salary-incomes/<str:income_tax_return_id>/', SalaryIncomeListCreateApi.as_view(),
         name='salary-income-list-create'),
    path('salary-incomes/<str:income_tax_return_id>/update/', SalaryIncomeUpdateApi.as_view(),
         name='salary-income-update'),
    path('rental-incomes/<str:income_tax_return_id>/', RentalIncomeListCreateApi.as_view(),
         name='rental-income-list-create'),
    path('rental-incomes/<str:income_tax_return_id>/update/', RentalIncomeUpdateApi.as_view(),
         name='rental-income-update'),
    path('capital-gains/<str:income_tax_return_id>/', CapitalGainsListCreateApi.as_view(),
         name='capital-gains-list-create'),
    path('capital-gains/<str:income_tax_return_id>/update/', CapitalGainsUpdateApi.as_view(),
         name='capital-gains-update'),
    path('business-incomes/<str:income_tax_return_id>/', BusinessIncomeListCreateApi.as_view(),
         name='business-income-list-create'),
    path('business-incomes/<str:income_tax_return_id>/update/', BusinessIncomeUpdateApi.as_view(),
         name='business-income-update'),
    path('agriculture-and-exempt-incomes/<str:income_tax_return_id>/', AgricultureAndExemptIncomeApi.as_view(),
         name='agriculture-and-exempt-incomes'),
    path('other-incomes/<str:income_tax_return_id>/', OtherIncomesApi.as_view(), name='other-incomes'),
    path('tax-paid/<str:income_tax_return_id>/', TaxPaidApi.as_view(), name='tax-paid'),
    path('deductions/<str:income_tax_return_id>/', DeductionsApi.as_view(), name='deductions'),
    path('total-income/<str:income_tax_return_id>/', TotalIncomeGetAPIView.as_view(), name='total-income-get-api'),
    path('total-tax-summary/<str:income_tax_return_id>/', TotalSummaryGetAPI.as_view(), name='total-tax-summary'),
    path('upload-ais-pdf/<str:income_tax_return_id>/', AISPdfUploadApi.as_view(), name='upload-ais-pdf'),
    path('upload-26as-pdf/<str:income_tax_return_id>/', TdsPdfUploadApi.as_view(), name='upload-26as-pdf'),
    path('upload-challan-pdf/<str:income_tax_return_id>/', ChallanUploadApi.as_view(), name='upload-challan-pdf'),
    path('update-challan-pdf/<str:income_tax_return_id>/', ChallanUploadApi.as_view(), name='update-challan-pdf'),
    path('reports-page/', ReportsPageAPIView.as_view(), name='reports-page'),
    path('reports-page/<str:income_tax_return_year_name>/', ReportsPageAPIView.as_view(), name='reports-specific-year'),
    path('income-tax-return-years/', IncomeTaxReturnYearListAPIView.as_view(), name='income-tax-return-years'),
    path('download-26as/<str:income_tax_return_year_name>/', Download26ASAPIView.as_view(), name='download-26as'),
    path('download-ais/<str:income_tax_return_year_name>/', DownloadAISAPIView.as_view(), name='download-ais'),
    path('download-tis/<str:income_tax_return_year_name>/', DownloadTISAPIView.as_view(), name='download-tis'),
    path('tax-refund/<str:income_tax_return_id>/', TaxRefundAPIView.as_view(), name='tax-refund'),
    path('computations-old-regime/<str:income_tax_return_id>/', ComputationsOldRegimeApi.as_view(), name='computations-old-regime'),
    path('computations-new-regime/<str:income_tax_return_id>/', ComputationsNewRegimeApi.as_view(), name='computations-new-regime'),
    path('tax-summary/<str:income_tax_return_id>/', SummaryPageApi.as_view(), name='tax-summary'),
    path('computations/<str:income_tax_return_id>/', ComputationsCreateApi.as_view(), name='create_computation'),
    path('itr-summary-pdf/<str:income_tax_return_id>/', IncomeTaxPdfView.as_view(), name='itr-summary-pdf'),
    path('itr-computations-old-pdf/<str:income_tax_return_id>/', IncometaxComputationsOldPdfView.as_view(), name='itr-computations-old-pdf'),
    path('itr-computations-new-pdf/<str:income_tax_return_id>/', IncometaxComputationsNewPdfView.as_view(), name='itr-computations-new-pdf'),
]
