
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from accounts.serializers.member import *
from accounts.serializers.auth import MemberSerializer

class InitialRegister(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cur_user = request.user
        serializer = InitialInfoRegisterSerializer(cur_user, request.data)
        if not cur_user.is_registered and serializer.is_valid():
            save_result = serializer.save()
            if save_result:
                return Response(MemberSerializer(serializer.data), status.HTTP_200_OK)
            else:
                return Response(status.HTTP_409_CONFLICT)
        else:
            return Response(status.HTTP_400_BAD_REQUEST)