from rest_framework import serializers
from .models import Person

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        exclude = ['private_note']
        read_only_fields = ['face_image']
