
from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from rest_framework.decorators import permission_classes, api_view
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny

from accounts.serializers.member import *
from accounts.serializers.auth import MemberSerializer, MediaImageSerializer
from accounts.models import Member, Tweet, FavoriteTweet

class InitialRegister(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cur_user = request.user
        serializer = InitialInfoRegisterSerializer(cur_user, request.data)
        if not cur_user.is_registered and serializer.is_valid():
            if Member.objects.exclude(id = cur_user.id).filter(nickname = request.data['nickname']).count() > 0:
                return Response(status = status.HTTP_409_CONFLICT)
            updated_user = serializer.save()
            return Response(MemberSerializer(updated_user).data, status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

class TweetView(mixins.DestroyModelMixin, mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetSerializer
    pagination_class = TweetPagination

    def get_queryset(self):
        return Tweet.objects.order_by("-created_at")
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_tweet(request):
    cur_user = request.user
    try:
        target_id = request.data['id']
        cur_tweet = Tweet.objects.get(pk = target_id)
        if FavoriteTweet.objects.filter(liker = cur_user, tweet = cur_tweet).count() > 0:
            FavoriteTweet.objects.filter(liker = cur_user, tweet = cur_tweet).delete()
        else:
            FavoriteTweet.objects.create(liker = cur_user, tweet = cur_tweet)
        likers_id = cur_tweet.tweet_likers.all().order_by('-created_at').values_list('liker')
        like_users = MainInfoSerializer(Member.objects.filter(id__in = likers_id, is_registered = True), many = True)    
        return Response(like_users.data)
    except Exception as e:
        return Response(status.HTTP_400_BAD_REQUEST)

class AvatarView(mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarSerializer

    def post(self, request, *args, **kwargs):
        avatar_serializer = self.get_serializer(data = request.data)
        if avatar_serializer.is_valid():
            new_avatar = avatar_serializer.save()
            user = request.user
            user.avatars.add(new_avatar)
            return Response(MediaImageSerializer(user.avatars, many = True).data, status = status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        avatar_serializer = self.get_serializer(instance = Media.objects.get(pk = pk), data = request.data)
        if avatar_serializer.is_valid():
            new_avatar = avatar_serializer.save()
            user = request.user
            return Response(MediaImageSerializer(user.avatars, many = True).data, status = status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        user = request.user
        user.avatars.remove(Media.objects.get(pk = pk))
        Media.objects.get(pk = pk).delete()
        return Response(MediaImageSerializer(user.avatars, many = True).data, status = status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_avatar_order(request):
    serializer = AvatarChangerSerializer(data = request.data)
    if serializer.is_valid():
        uris_data = serializer.validated_data
        cur_user = request.user
        cur_user.avatars.clear()
        for uri_item in uris_data['uris']:
            media_obj = Media.objects.create(uri = uri_item)
            cur_user.avatars.add(media_obj)
        return Response(MediaImageSerializer(cur_user.avatars, many = True).data, status = status.HTTP_200_OK)
    else:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_line(request):
    if 'line_id' in request.data.keys():
        line_id = request.data.get('line_id')
        cur_user = request.user
        if Member.objects.exclude(pk = cur_user.id).filter(line_id = line_id).count() > 0:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            cur_user.line_id = line_id
            cur_user.save()
            return Response(status = status.HTTP_200_OK)
    else:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChange(data = request.data)
    if serializer.is_valid():
        input_data = serializer.validated_data
        old_pwd = input_data.get('old', "")
        new_pwd = input_data.get('new', "")
        confirm_pwd = input_data.get('confirm', "")
        user = request.user
        if old_pwd != "":
            if not user.check_password(old_pwd):
                return Response(status = status.HTTP_400_BAD_REQUEST)
        user.set_password(new_pwd)
        return Response(status = status.HTTP_200_OK)
    else:
        return Response(status = status.HTTP_400_BAD_REQUEST)

class DetailView(APIView):

    def post(self, request):
        serializer = DetailSerializer(data = request.data, partial = True)
        if serializer.is_valid():
            detail_obj = serializer.save()
            user = request.user
            user.detail = detail_obj
            user.save()
            return Response(DetailSerializer(detail_obj).data, status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        detail_obj = Detail.objects.get(pk = pk)
        serializer = DetailSerializer(detail_obj, data = request.data, partial = True)
        if serializer.is_valid():
            detail_obj = serializer.save()
            user = request.user
            user.detail = detail_obj
            user.save()
            return Response(DetailSerializer(detail_obj).data, status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfileSerializer(request.user, data = request.data, partial = True)        
        user = request.user
        if serializer.is_valid():
            new_nickname = request.data.get('nickname', "")
            if Member.objects.exclude(id = user.id).filter(nickname = new_nickname).count() > 0:
                return Response(status = status.HTTP_409_CONFLICT)
            updated_user = serializer.save()
            return Response(MemberSerializer(updated_user).data, status = status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

class AdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        admins = Member.objects.filter(role__lt = 0)
        return Response(MemberSerializer(admins, many = True).data)

class MemberView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        is_all = int(request.GET.get("is_all", "0"))
        if is_all > 0:
            members = Member.objects.filter(is_registered = True)
        else:
            members = Member.objects.filter(role__gte = 0, is_registered = True)
        return Response(MemberSerializer(members, many = True).data)