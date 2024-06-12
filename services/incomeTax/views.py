from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxBankDetails
from services.incomeTax.serializers import IncomeTaxProfileSerializer, IncomeTaxBankDetailsSerializer


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