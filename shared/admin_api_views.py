# from rest_framework.generics import (
#     CreateAPIView as RestCreateAPIView, RetrieveAPIView as RestRetrieveAPIView,
#     UpdateAPIView as RestUpdateAPIView, DestroyAPIView as RestDestroyAPIView,
#     ListAPIView as RestListAPIView
# )
# from rest_framework.views import APIView as RestAPIView
#
# from accounts.mixins import AdminPermissionMixin
# from bichhoos.commons import (
#     api_views as common_api_views,
#     api_conditions as common_api_conditions,
# )
#
#
# # These are the api_views that are to be used for Admin panel APIs.
# class CrudAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, common_api_views.CrudAPIView):
#     pass
#
#
# class CreateAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestCreateAPIView):
#     pass
#
#
# class RetrieveAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestRetrieveAPIView):
#     pass
#
#
# class UpdateAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestUpdateAPIView):
#     pass
#
#
# class DestroyAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestDestroyAPIView):
#     pass
#
#
# class ListAPIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestListAPIView):
#     pass
#
#
# class APIView(AdminPermissionMixin, common_api_conditions.CustomAPIConditions, RestAPIView):
#     pass
