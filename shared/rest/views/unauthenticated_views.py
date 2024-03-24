from rest_framework import (
    generics,
    views,
    viewsets,
    permissions
)

from shared.libs.hashing import AlphaId


class CommonOverrides:
    permission_classes = (permissions.AllowAny,)

    def initialize_request(self, request, *args, **kwargs):
        if 'pk' in self.kwargs:
            self.kwargs['pk'] = AlphaId.decode(self.kwargs['pk'])
        return super().initialize_request(request, *args, **kwargs)


class APIView(CommonOverrides, views.APIView):
    ...


class GenericAPIView(CommonOverrides, generics.GenericAPIView):
    ...


class CreateAPIView(CommonOverrides, generics.CreateAPIView):
    ...


class UpdateAPIView(CommonOverrides, generics.UpdateAPIView):
    ...


class RetrieveAPIView(CommonOverrides, generics.RetrieveAPIView):
    ...


class DestroyAPIView(CommonOverrides, generics.DestroyAPIView):
    ...


class ListAPIView(CommonOverrides, generics.ListAPIView):
    ...


class ModelViewSet(CommonOverrides, viewsets.ModelViewSet):
    ...


class ReadOnlyModelViewSet(CommonOverrides, viewsets.ReadOnlyModelViewSet):
    ...
