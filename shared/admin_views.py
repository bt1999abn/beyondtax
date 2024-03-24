# from rest_framework.generics import (
#     CreateAPIView as RestCreateAPIView, RetrieveAPIView as RestRetrieveAPIView,
#     UpdateAPIView as RestUpdateAPIView, DestroyAPIView as RestDestroyAPIView,
#     ListAPIView as RestListAPIView
# )
# from rest_framework.views import APIView as RestAPIView
# from rest_framework import viewsets
#
# from accounts.mixins import AdminPermissionMixin
# from bichhoos.commons import (
#     api_views as common_api_views,
# )
#
#
# # These are the api_views that are to be used for Admin panel APIs.
# class CrudAPIView(AdminPermissionMixin, common_api_views.CrudAPIView):
#     pass
#
#
# class CreateAPIView(AdminPermissionMixin, RestCreateAPIView):
#     pass
#
#
# class RetrieveAPIView(AdminPermissionMixin, RestRetrieveAPIView):
#     pass
#
#
# class UpdateAPIView(AdminPermissionMixin, RestUpdateAPIView):
#     pass
#
#
# class DestroyAPIView(AdminPermissionMixin, RestDestroyAPIView):
#     pass
#
#
# class ListAPIView(AdminPermissionMixin, RestListAPIView):
#     pass
#
#
# class APIView(AdminPermissionMixin, RestAPIView):
#     pass
#
#
# class ModelViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
#     def create(self, request, *args, **kwargs):
#         if hasattr(self, 'save_case_insensitive'):
#             if hasattr(request.data, '_mutable'):
#                 request.data._mutable = True
#             for field in self.save_case_insensitive:
#                 if field in request.data:
#                     request.data[field] = request.data[field].lower()
#         return super().create(request, *args, **kwargs)
