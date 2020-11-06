
from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from rest_framework.decorators import permission_classes, api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from accounts.serializers.member import *
from accounts.serializers.auth import MemberSerializer
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

class TweetView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetSerializer
    pagination_class = TweetPagination

    def get_queryset(self):
        return Tweet.objects.order_by("-created_at")
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

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
