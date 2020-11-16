import json
from django.db.models.query import QuerySet
import jwt
from dateutil.relativedelta import relativedelta
import requests

from django.conf import settings

from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from rest_framework.decorators import permission_classes, api_view
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny, BasePermission

from accounts.serializers.member import *
from accounts.serializers.auth import MemberSerializer, MediaImageSerializer, DetailSerializer, TransferInfoSerializer
from accounts.models import Member, Tweet, FavoriteTweet, Detail
from basics.serializers import ChoiceSerializer


class IsSuperuserPermission(BasePermission):
    message = "Only superuser is allowed"

    def has_permission(self, request, view):
        return request.user.is_superuser

class IsCast(BasePermission):
    message = "Only Cast is allowed"

    def has_permission(self, request, view):
        return request.user.role == 0


class InitialRegister(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cur_user = request.user
        if cur_user.role == 10:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = InitialInfoRegisterSerializer(cur_user, request.data)
        if not cur_user.is_registered and serializer.is_valid():
            if Member.objects.exclude(id=cur_user.id).filter(nickname=request.data['nickname']).count() > 0:
                return Response(status=status.HTTP_409_CONFLICT)
            updated_user = serializer.save()
            return Response(MemberSerializer(updated_user).data, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TweetView(mixins.DestroyModelMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetSerializer
    pagination_class = TweetPagination

    def get_queryset(self):
        if self.request.user.role == 1:
            return Tweet.objects.filter(category = 0).order_by("-created_at")
        else:
            return Tweet.objects.order_by("-created_at")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_tweet(request):
    cur_user = request.user
    try:
        target_id = request.data['id']
        cur_tweet = Tweet.objects.get(pk=target_id)
        if FavoriteTweet.objects.filter(liker=cur_user, tweet=cur_tweet).count() > 0:
            FavoriteTweet.objects.filter(
                liker=cur_user, tweet=cur_tweet).delete()
        else:
            FavoriteTweet.objects.create(liker=cur_user, tweet=cur_tweet)
        likers_id = cur_tweet.tweet_likers.all().order_by(
            '-created_at').values_list('liker')
        like_users = MainInfoSerializer(Member.objects.filter(
            id__in=likers_id, is_registered=True), many=True)
        return Response(like_users.data)
    except Exception as e:
        return Response(status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def count_tweet(request):
    return Response(Tweet.objects.count(), status=status.HTTP_200_OK)


class AvatarView(mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarSerializer

    def post(self, request, *args, **kwargs):
        avatar_serializer = self.get_serializer(data=request.data)
        if avatar_serializer.is_valid():
            new_avatar = avatar_serializer.save()
            user = request.user
            user.avatars.add(new_avatar)
            return Response(MediaImageSerializer(user.avatars, many=True).data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        avatar_serializer = self.get_serializer(
            instance=Media.objects.get(pk=pk), data=request.data)
        if avatar_serializer.is_valid():
            new_avatar = avatar_serializer.save()
            user = request.user
            return Response(MediaImageSerializer(user.avatars, many=True).data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        user = request.user
        user.avatars.remove(Media.objects.get(pk=pk))
        Media.objects.get(pk=pk).delete()
        return Response(MediaImageSerializer(user.avatars, many=True).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_avatar_order(request):
    serializer = AvatarChangerSerializer(data=request.data)
    if serializer.is_valid():
        uris_data = serializer.validated_data
        cur_user = request.user
        cur_user.avatars.clear()
        for uri_item in uris_data['uris']:
            media_obj = Media.objects.create(uri=uri_item)
            cur_user.avatars.add(media_obj)
        return Response(MediaImageSerializer(cur_user.avatars, many=True).data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_line(request):
    if 'code' in request.data.keys():
        line_code = request.data.get('code')

        url = "https://api.line.me/oauth2/v2.1/token"

        payload = 'grant_type=authorization_code' + \
            '&code=' + line_code + \
            '&redirect_uri=' + settings.CLIENT_URL + '/main/mypage/help/signin-method' + \
            '&client_id=' + settings.LINE_CLIENT_ID + \
            '&client_secret=' + settings.LINE_CLIENT_SECRET

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload)

        id_token = json.loads(
            response.text.encode('utf8')).get('id_token', '')

        try:
            decoded_payload = jwt.decode(id_token, None, None)
            line_id = decoded_payload['sub']

            cur_user = request.user

            if Member.objects.exclude(pk=cur_user.id).filter(social_id=line_id).count() > 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                cur_user.social_id = line_id
                cur_user.save()
                return Response(status=status.HTTP_200_OK)

        except jwt.exceptions.InvalidSignatureError:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChange(data=request.data)
    if serializer.is_valid():
        input_data = serializer.validated_data
        old_pwd = input_data.get('old', "")
        new_pwd = input_data.get('new', "")
        confirm_pwd = input_data.get('confirm', "")
        user = request.user
        if old_pwd != "":
            if not user.check_password(old_pwd):
                return Response(status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_pwd)
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DetailView(APIView):

    def post(self, request):
        serializer = DetailSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            detail_obj = serializer.save()
            user = request.user
            user.detail = detail_obj
            user.save()
            return Response(DetailSerializer(detail_obj).data, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        detail_obj = Detail.objects.get(pk=pk)
        serializer = DetailSerializer(
            detail_obj, data=request.data, partial=True)
        if serializer.is_valid():
            detail_obj = serializer.save()
            user = request.user
            user.detail = detail_obj
            user.save()
            return Response(DetailSerializer(detail_obj).data, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfileSerializer(
            request.user, data=request.data, partial=True)
        user = request.user
        if serializer.is_valid():
            new_nickname = request.data.get('nickname', "")
            if Member.objects.exclude(id=user.id).filter(nickname=new_nickname).count() > 0:
                return Response(status=status.HTTP_409_CONFLICT)
            updated_user = serializer.save()
            return Response(MemberSerializer(updated_user).data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AdminView(mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = [IsSuperuserPermission]
    serializer_class = AdminSerializer
    pagination_class = AdminPagination

    def get_queryset(self):
        return Member.objects.filter(role__lt=0, is_superuser=False)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class MemberView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.db.models import Q

        is_all = int(request.GET.get("is_all", "0"))
        is_cast = int(request.GET.get("is_cast", "0"))
        if is_all > 0:
            members = Member.objects.filter(Q(is_registered=True, is_active = True, role__gte = 0) | Q(role__lt = 0))
        elif is_cast > 0:
            members = Member.objects.filter(is_registered=True, role = 0)
        else:
            members = Member.objects.filter(role__gte=0, is_registered=True, is_active = True)
        return Response(MemberSerializer(members, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_fresh_casts(request):
    from dateutil.relativedelta import relativedelta

    today = datetime.now()
    three_months_ago = today - relativedelta(months=3)

    casts = Member.objects.filter(role=0, cast_started_at__gt=three_months_ago)
    return Response(GeneralInfoSerializer(casts, many=True).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_casts(request):
    serializer = CastFilterSerializer(data=request.GET, partial=True)
    if serializer.is_valid():
        input_data = serializer.validated_data
        queryset = Member.objects.filter(
            role=0, is_active=True, is_registered=True)
        page = input_data.get('page', 1)
        size = 10

        # location = input_data.get('location', 0)
        # if location > 0:
        #     queryset = queryset.filter()

        cast_class = input_data.get('cast_class', 0)
        if cast_class > 0:
            queryset = queryset.filter(cast_class__id=cast_class)

        nickname = input_data.get('nickname', "")
        if nickname != "":
            queryset = queryset.filter(nickname__icontains=nickname)

        # is new
        is_new = input_data.get('is_new', False)
        if is_new:
            today = datetime.now()
            three_months_ago = today - relativedelta(months=3)
            queryset = queryset.filter(cast_started_at__gt=three_months_ago)

        # point min and max
        point_min = input_data.get('point_min', 0)
        queryset = queryset.filter(point_half__gte=point_min)

        point_max = input_data.get('point_max', 30000)
        queryset = queryset.filter(point_half__lte=point_max)

        # choices
        choices = input_data.get('choices', [])
        for choice_item in choices:
            queryset = queryset.filter(cast_status__id=choice_item)

        start_index = (page - 1) * size

        return Response(
            GeneralInfoSerializer(
                queryset.order_by("-cast_started_at")
                .all()[(start_index):(start_index + size)],
                many=True
            ).data,
            status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_guests(request):
    serializer = GuestFilterSerializer(data=request.GET, partial=True)
    if serializer.is_valid():
        input_data = serializer.validated_data
        queryset = Member.objects.filter(
            role=1, is_active=True, is_registered=True)
        page = input_data.get('page', 1)
        size = 10
        start_index = (page - 1) * size

        # age min and max
        year_now = datetime.now().year
        age_min = input_data.get('age_min', 20)
        age_max = input_data.get('age_max', 50)
        year_min = year_now - age_max
        year_max = year_now - age_min + 1

        from_date = datetime(year_min, 1, 1, 0, 0, 0)
        to_date = datetime(year_max, 1, 1, 0, 0, 0)
        queryset = queryset.filter(
            birthday__gte=from_date, birthday__lt=to_date)

        # nickname
        nickname = input_data.get('nickname', "")
        if nickname != "":
            queryset = queryset.filter(nickname__icontains=nickname)

        # salary
        salary = input_data.get('salary', 0)
        if salary > 0:
            queryset = queryset.filter(detail__annual=salary)

        # favorite
        favorite = input_data.get('favorite', "")
        if favorite != "":
            queryset = queryset.filter(favorite__icontains=favorite)

        return Response(
            GeneralInfoSerializer(
                queryset.order_by("-guest_started_at")
                .all()[(start_index):(start_index + size)],
                many=True
            ).data,
            status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def edit_choice(request):
    choice_serializer = ChoiceIdSerializer(data=request.data)
    if choice_serializer.is_valid():
        user = request.user
        choice_data = choice_serializer.validated_data
        user.cast_status.clear()
        user.cast_status.set(choice_data.get('choice'))
        user.save()
        return Response(ChoiceSerializer(user.cast_status, many=True).data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsCast])
def apply_transfer(request):
    import math
    cur_user = request.user
    amount = request.user.point - 440 - math.ceil(request.user.point / 50)
    if amount < 0:
        return Response(status = status.HTTP_400_BAD_REQUEST)
    else:
        TransferApplication.objects.create(
            location = cur_user.location,
            user = cur_user,
            amount = amount,
            point = request.user.point,
            apply_type = 1,
            currency_type = 'jpy'
        )
        return Response(status = status.HTTP_200_OK)

class TransferView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsSuperuserPermission]
    serializer_class = TransferSerializer
    pagination_class = TransferPagination

    def get_queryset(self):
        return TransferApplication.objects.order_by("-created_at")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class TransferInfoView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsCast, IsSuperuserPermission]
    serializer_class = TransferInfoSerializer
    