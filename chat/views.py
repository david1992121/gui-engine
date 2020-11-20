"""
APIs for Chat
"""
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count

# from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notice, Room
from .serializers import NoticeSerializer, RoomSerializer


# def index(request):
#     return render(request, 'chat/index.html', {})


# def room(request, room_name):
#     return render(request, 'chat/room.html', {
#         'room_name': room_name
#     })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notices_list(request):
    """
    List all notices by user, or create a new notice.
    """

    if request.method == 'GET':
        notices = Notice.objects.filter(
            user=request.user,
            notice_type=request.GET.get('notice_type', 'foot')
        )
        paginator = Paginator(notices.order_by('-created_at'), 10)
        try:
            paginated_notices = paginator.page(request.GET.get('page', 1))
            return Response(
                data=NoticeSerializer(paginated_notices, many=True).data,
                status=status.HTTP_200_OK
            )
        except EmptyPage:
            return Response(
                data=[],
                status=status.HTTP_200_OK
            )

    elif request.method == 'POST':
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            new_notice = serializer.save()
            return Response(
                data=NoticeSerializer(new_notice).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rooms_list(request):
    """
    List all rooms by user.
    """

    if request.method == 'GET':
        mode = request.GET.get('mode', 'all')
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', 1)
        offset = request.GET.get('offset', 0)
        page_size = 10
        start_index = offset + page * page_size

        # initial queryset
        query_set = request.user.rooms

        # mode is group or all
        if mode == "group":
            query_set = query_set.filter(is_group = True)
        
        # get rooms
        rooms = Room.objects.filter(id__in = list(query_set.values_list('id', flat = True)))

        # nickname search       
        if keyword != "":
            rooms = rooms.filter(users__nickname__icontains = keyword)

        # order by created at and pagination
        rooms = rooms.order_by('-updated_at').all()[start_index:start_index + page_size]
        rooms = rooms.annotate(unread = Count('messages', filter = Q(messages__receiver = request.user) & Q(messages__is_read = False)))
        return Response(
            RoomSerializer(rooms, many = True).data,
            status.HTTP_200_OK
        )
