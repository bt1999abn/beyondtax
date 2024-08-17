from payments.models import Payment
from shared.rest.serializers import BaseModelSerializer


class PaymentSerializer(BaseModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'
        