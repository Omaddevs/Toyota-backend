from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import UserSerializer


class ToyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT javobiga `user` obyektini qo‘shadi (frontend kutilgan format)."""

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
