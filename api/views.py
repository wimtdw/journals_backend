from rest_framework import serializers, generics
from django.db import IntegrityError
from rest_framework import viewsets, exceptions
from django.contrib.auth import get_user_model
from posts.models import Journal, Post
from .serializers import (PostSerializer,
                          FollowSerializer,
                          JournalSerializer)
from rest_framework import mixins
from rest_framework import filters
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.decorators import action
from djoser.serializers import UserSerializer


User = get_user_model()


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    search_fields = ('text',)
    filterset_fields = ('author__username', 'journal')

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Post.objects.filter(is_private=False)
        user = self.request.user
        queryset = Post.objects.filter(
            Q(author=user) | Q(author__isnull=False, is_private=False)
        ).distinct()

        return queryset

    def perform_create(self, serializer):
        journal = serializer.validated_data.get('journal')
        if journal.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Добавлять посты можно только в свои журналы!')
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Изменение чужого контента запрещено!')
        serializer.save(author=self.request.user)

    def perform_destroy(self, serializer):
        instance = self.get_object()
        if instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Удаление чужого контента запрещено!')
        instance.delete()


class JournalViewSet(viewsets.ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author__username',)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Journal.objects.filter(is_private=False)
        user = self.request.user
        queryset = Journal.objects.filter(
            Q(author=user) | Q(author__isnull=False, is_private=False)
        ).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Изменение чужого контента запрещено!')
        serializer.save(author=self.request.user)

    def perform_destroy(self, serializer):
        instance = self.get_object()
        if instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Удаление чужого контента запрещено!')
        instance.delete()

    @action(detail=True, methods=['post'], url_path='check-pin', url_name='check-pin')
    def check_pin(self, request, pk=None):
        journal = self.get_object()
        pin = request.data.get('pin', '')

        if not journal.is_private:
            return Response(
                {"detail": "Journal is not private"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if journal.check_pin(pin):
            return Response({'valid': True})

        return Response({'valid': False}, status=status.HTTP_403_FORBIDDEN)


class CreateListViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    pass


class FollowViewSet(CreateListViewSet):
    serializer_class = FollowSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (permissions.IsAuthenticated,)
    search_fields = ('following__username',)

    def get_queryset(self):
        user = self.request.user
        new_queryset = user.following.all()
        return new_queryset

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise serializers.ValidationError(
                {"error": "Вы уже подписаны на этого пользователя!"}
            )


class JournalExportAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        try:
            journal = Journal.objects.get(pk=pk)
        except Journal.DoesNotExist:
            return Response(
                {"error": "Journal not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if journal.author != request.user:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        content = [
            f"Дневник: {journal.title}",
            f"Описание: {journal.description or '-'}",
            f"Создан: {journal.pub_date.strftime('%d.%m.%Y %H:%M')}",
            f"Изменен: {journal.last_modified.strftime('%d.%m.%Y %H:%M')}",
            f"Автор: {journal.author.username}",
            "\nЗаписи:"
        ]

        for i, post in enumerate(journal.posts.all().order_by('pub_date'), 1):
            content.append(
                f"{i}. {post.text}\n"
                f"Дата создания: {post.pub_date.strftime('%d.%m.%Y %H:%M')}\n"
            )

        response = HttpResponse('\n'.join(content), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{journal.title}_export.txt"'
        return response


class UserListView(generics.ListAPIView):
    '''
    ViewSet для поиска пользователей
    '''
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['^username']
