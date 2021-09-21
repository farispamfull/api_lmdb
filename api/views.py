from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from .filters import TitleFilter
from .models import Title
from .permissions import ReadOnly
from .serializer import (SignUpSerializer, TokenSerializer, TitleSerializer,
                         TitlePostSerializer)
from .utils import send_token_for_user


class SignUpApiView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        user, _ = User.objects.get_or_create(
            email=email, username=username,
            is_active=False
        )
        send_token_for_user(request, user)

        return Response({'email': email}, status=status.HTTP_200_OK)


class EmailConfirmationView(APIView):
    serializer_class = TokenSerializer

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email=serializer.data['email'])
        confirmation_code = serializer.data['confirmation_code']
        if default_token_generator.check_token(user, confirmation_code):
            user.is_active = True
            user.save()
            token = self.get_token(user)
            return Response({'token': token}, status=status.HTTP_200_OK)

        response = {'confirmation_code': 'invalid confirmation code'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).order_by('rating')

    permission_classes = [IsAuthenticated & IsAdminUser | ReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleSerializer
        return TitlePostSerializer
