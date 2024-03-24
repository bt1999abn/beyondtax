from rest_framework.generics import (
    CreateAPIView as RestCreateAPIView, UpdateAPIView, DestroyAPIView, ListAPIView
)


class CrudAPIView(RestCreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView):
    def create(self, request, *args, **kwargs):
        if hasattr(self, 'save_case_insensitive'):
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
            for field in self.save_case_insensitive:
                if field in request.data:
                    request.data[field] = request.data[field].lower()
        return super().create(request, *args, **kwargs)


class CreateAPIView(RestCreateAPIView):
    pass

