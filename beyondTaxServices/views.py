from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ServicePagesSerializer
from accounts.models import ServicePages


class ServicePagesApi(APIView):
    def get(self, request, *args, **kwargs):
        slug = request.GET.get('slug')
        if not slug:
            return Response({"error":  "Slug parameter is required."}, status=400)
        queryset = ServicePages.objects.get(slug=slug)
        if queryset is None:
            return Response({"message": "Service Page not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServicePagesSerializer(queryset, many=False)
        return Response({'data': serializer.data})
