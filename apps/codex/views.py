from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClubCodex
from .serializers import ClubCodexSerializer


class ClubCodexView(APIView):
    """Раздел 1 плана: Кодекс цеха, публичное чтение. Редактирование — только

    через Django admin (единый устав, редкое и значимое действие).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(ClubCodexSerializer(ClubCodex.load()).data)
