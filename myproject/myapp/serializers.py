from rest_framework import serializers
from myapp.models import EnfermeroPastillero, Enfermero
from mongoengine import Document
from mongoengine.fields import StringField, DictField, ListField, ReferenceField

class PastilleroSerializer(serializers.Serializer):
    id = serializers.CharField()
    codigo = serializers.CharField()
    ubicacion = serializers.DictField()
    Datos_Sensores = serializers.ListField()
    estado = serializers.DictField()
    enfermeros_autorizados = serializers.ListField()

class EnfermeroSerializer(serializers.ModelSerializer):
    pastilleros = serializers.SerializerMethodField()

    class Meta:
        model = Enfermero
        fields = ['id', 'nombre', 'apellidos', 'pastilleros']

    def get_pastilleros(self, obj):
        from myapp.models import Pastillero
        pastillero_ids = obj.pastilleros.values_list('pastillero_id', flat=True)
        return PastilleroSerializer(Pastillero.objects(id__in=pastillero_ids), many=True).data
