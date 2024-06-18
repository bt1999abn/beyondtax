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

    def get(self, request):
        try:
            profile = IncomeTaxProfile.objects.get(user=request.user)
        except IncomeTaxProfile.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

        serializer = IncomeTaxProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


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