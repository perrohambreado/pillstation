from rest_framework import serializers
from .models import PillStation

class PillStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillStation
        fields = '__all__'