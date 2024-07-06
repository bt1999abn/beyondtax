from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from services.incomeTax.models import IncomeTaxProfile, IncomeTaxReturn, IncomeTaxReturnYears, ResidentialStatusQuestions
from services.incomeTax.serializers import IncomeTaxProfileSerializer, \
    IncomeTaxReturnSerializer, ResidentialStatusQuestionsSerializer


class IncomeTaxProfileApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            profile = IncomeTaxProfile.objects.get(user=user)
            profile_serializer = IncomeTaxProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        except IncomeTaxProfile.DoesNotExist:
            profile_serializer = IncomeTaxProfileSerializer(data=request.data, context={'request': request})

        if profile_serializer.is_valid():
            profile, next_question_data = profile_serializer.save()
            response_serializer = IncomeTaxProfileSerializer(profile, context={'request': request})
            response_data = response_serializer.data
            response_data['next_question'] = next_question_data

            if next_question_data and "id" in next_question_data:
                return Response({
                    "status_code": 200,
                    "status_text": "OK",
                    "data": response_data
                }, status=status.HTTP_200_OK)

            return Response({
                "status_code": 201,
                "status_text": "Created",
                "data": response_data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status_code": 400,
            "status_text": "Bad Request",
            "errors": profile_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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


class ResidentialStatusQuestionsListView(APIView):
    def get(self, request, format=None):
        questions = ResidentialStatusQuestions.objects.all()
        serializer = ResidentialStatusQuestionsSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)