from posts.models import Post, Follow, Journal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.relations import SlugRelatedField
import base64
from django.core.files.base import ContentFile

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class PostSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = Base64ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        journal = attrs.get('journal')
        if journal and journal.is_private and attrs.get('is_private') is False:
            raise serializers.ValidationError(
                "Posts in a private journal must be private.")
        return attrs

    class Meta:
        fields = '__all__'
        model = Post


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
    is_pin_set = serializers.SerializerMethodField()

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
            'pin',
            'is_pin_set'
        ]
        read_only_fields = ['pub_date',
                            'last_modified', 'author', 'is_pin_set']

    def get_is_pin_set(self, obj):
        return obj.pin_code is not None

    def validate_pin(self, value):
        if value:
            if not value.isdigit():
                raise serializers.ValidationError(
                    "PIN должен содержать только цифры.")
            if not (4 <= len(value) <= 6):
                raise serializers.ValidationError(
                    "PIN должен содержать от 4 до 6 цифр.")
        return value or None

    def validate(self, data):
        is_private = data.get('is_private')
        if self.instance and is_private is None:
            is_private = self.instance.is_private
        else:
            is_private = data.get('is_private', False)

        pin = data.get('pin', None)
        if not is_private and pin not in (None, ''):
            raise serializers.ValidationError({
                "pin": "PIN cannot be set for a non-private journal."
            })

        if not is_private:
            data['pin'] = None

        return data

    def create(self, validated_data):
        pin = validated_data.pop('pin', None)
        journal = Journal.objects.create(**validated_data)
        journal.set_pin(pin)
        journal.save()
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
