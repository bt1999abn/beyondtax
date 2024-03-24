from rest_framework import generics


class ListRetrieveAPIView(generics.RetrieveAPIView, generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        if kwargs.get("pk"):
            return self.retrieve(request, *args, **kwargs)
        else:
            return self.list(request, *args, **kwargs)
