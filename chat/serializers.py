from rest_framework import serializers

from accounts.serializers.member import MainInfoSerializer
from chat.models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    """
    Notice Serializer
    """
    user_id = serializers.IntegerField()
    from_user_id = serializers.IntegerField()
    user = MainInfoSerializer(read_only=True)
    from_user = MainInfoSerializer(read_only=True)

    class Meta:
        model = Notice
        fields = (
            'id',
            'content',
            'user_id',
            'from_user_id',
            'user',
            'from_user',
            'notice_type',
            'created_at'
        )
        extra_keywords = {
            'user_id': {
                'write_only': True,
                'required': True
            },
            'from_user_id': {
                'write_only': True,
                'required': True
            }
        }
