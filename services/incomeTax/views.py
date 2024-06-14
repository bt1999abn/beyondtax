from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails, IncomeTaxReturn, IncomeTaxReturnYears
from services.incomeTax.serializers import IncomeTaxProfileSerializer, IncomeTaxBankDetailsSerializer, \
    IncomeTaxReturnSerializer


class IncomeTaxProfileApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IncomeTaxProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            profile = IncomeTaxProfile.objects.get(user=request.user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = IncomeTaxProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncomeTaxBankDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, income_tax_pk=None):
        user = request.user
        try:
            income_tax_profile = IncomeTaxProfile.objects.get(user=user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({'message': 'User does not have an Income Tax Profile'}, status=status.HTTP_404_NOT_FOUND)
        if income_tax_pk:
            try:
                bank_details = IncomeTaxBankDetails.objects.filter(income_tax=income_tax_profile.pk, pk=income_tax_pk)
            except ValueError:
                return Response({'error': 'Invalid income tax profile ID'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            bank_details = IncomeTaxBankDetails.objects.filter(income_tax=income_tax_profile)

        serializer = IncomeTaxBankDetailsSerializer(bank_details, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = IncomeTaxBankDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            bank_details = IncomeTaxBankDetails.objects.get(pk=pk)
        except IncomeTaxBankDetails.DoesNotExist:
            return Response({'error': 'Bank details not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = IncomeTaxBankDetailsSerializer(bank_details, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            bank_details = IncomeTaxBankDetails.objects.get(pk=pk)
        except IncomeTaxBankDetails.DoesNotExist:
            return Response({'error': 'Bank details not found'}, status=status.HTTP_404_NOT_FOUND)

        bank_details.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListIncomeTaxReturnsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        income_tax_returns = IncomeTaxReturn.objects.filter(user=user).order_by('-income_tax_return_year__start_date')
        if not income_tax_returns.exists():
            income_tax_return_years = IncomeTaxReturnYears.objects.all()
            for year in income_tax_return_years:
                IncomeTaxReturn.objects.create(
                    user=user,
                    income_tax_return_year=year,
                    status=IncomeTaxReturn.NotFiled
                )
        serializer = IncomeTaxReturnSerializer(income_tax_returns, many=True)
        return Response({'status_code': 200, 'status_text': 'OK', 'data': serializer.data})