from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import JournalViewSet, PostViewSet, FollowViewSet, JournalExportAPIView, UserListView


router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register(r'journals', JournalViewSet, basename='journal')
router.register('follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        'v1/journals/<int:pk>/export/',
        JournalExportAPIView.as_view(),
        name='journal-export'
    ),
    path('v1/users/search/', UserListView.as_view(), name='user-search'),
    path('v1/', include('djoser.urls')),
    path('v1/', include('djoser.urls.jwt')),
]
