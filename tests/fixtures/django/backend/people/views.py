import logging
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import PersonSerializer
from .models import Person

logger = logging.getLogger(__name__)

class PersonView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data['email']
        logger.info('email %s', request.data['email'])
        serializer = PersonSerializer(data=request.data)
        serializer.save()
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'ok': True})

class PersonViewSet:
    serializer_class = PersonSerializer
    def list(self, request):
        serializer = PersonSerializer(Person.objects.all(), many=True)
        return Response(serializer.data)
    def create(self, request):
        Person.objects.create(email=request.data['email'])
        return Response({'ok': True})
