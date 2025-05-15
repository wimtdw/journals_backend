from posts.models import Comment, Post, Follow, Journal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.relations import SlugRelatedField
import base64  # Модуль с функциями кодирования и декодирования base64
from django.core.files.base import ContentFile

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Если полученный объект строка, и эта строка
        # начинается с 'data:image'...
        if isinstance(data, str) and data.startswith('data:image'):
            # ...начинаем декодировать изображение из base64.
            # Сначала нужно разделить строку на части.
            format, imgstr = data.split(';base64,')
            # И извлечь расширение файла.
            ext = format.split('/')[-1]
            # Затем декодировать сами данные и поместить результат в файл,
            # которому дать название по шаблону.
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class PostSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    
    class Meta:
        fields = '__all__'
        model = Post


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    post = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        fields = '__all__'
        model = Comment


class JournalSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    pin = serializers.CharField(
        write_only=True,
        required=False,
        min_length=4,
        max_length=6,
        help_text="Необязательный PIN-код (4-6 цифр)",
        allow_blank=True
    )
    class Meta:
        model = Journal
        fields = [
            'id',
            'title',
            'description',
            'pub_date',
            'last_modified',
            'author',
            'image',
            'is_private',
            'pin'
        ]
        read_only_fields = ['pub_date', 'last_modified', 'author']

    def validate_pin(self, value):
        if value and (not value.isdigit() or len(value) < 4):
            raise serializers.ValidationError(
                "PIN должен содержать от 4 до 6 цифр."
            )
        return value or None

    def create(self, validated_data):
        pin = validated_data.pop('pin', None)
        journal = Journal.objects.create(**validated_data)
        journal.set_pin(pin)
        return journal

    def update(self, instance, validated_data):
        pin = validated_data.pop('pin', None)
        instance.set_pin(pin)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('pin_code', None)
        return representation


class FollowSerializer(serializers.ModelSerializer):
    user = SlugRelatedField(slug_field='username', read_only=True)
    following = SlugRelatedField(slug_field='username',
                                 queryset=User.objects.all())

    def validate(self, data):
        user = self.context['request'].user
        if data['following'] == user:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя!"
            )
        return data

    class Meta:
        fields = ('user', 'following')
        model = Follow
