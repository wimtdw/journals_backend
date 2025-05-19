import pytest

from posts.models import Follow, Post, Journal


@pytest.fixture
def group_1():
    return Journal.objects.create(title='Группа 1')


@pytest.fixture
def post(user, group_1):
    return Post.objects.create(
        text='Тестовый пост 1', author=user, journal=group_1
    )


@pytest.fixture
def post_2(user, group_1):
    return Post.objects.create(
        text='Тестовый пост 12342341', author=user, journal=group_1
    )


@pytest.fixture
def follow_1(user, another_user):
    return Follow.objects.create(user=user, following=another_user)


@pytest.fixture
def follow_2(user_2, user):
    return Follow.objects.create(user=user_2, following=user)


@pytest.fixture
def follow_3(user_2, another_user):
    return Follow.objects.create(user=user_2, following=another_user)


@pytest.fixture
def follow_4(another_user, user):
    return Follow.objects.create(user=another_user, following=user)


@pytest.fixture
def follow_5(user_2, user):
    return Follow.objects.create(user=user, following=user_2)
