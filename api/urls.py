from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import JournalViewSet, PostViewSet, CommentViewSet, FollowViewSet, JournalExportAPIView


router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register('journals', JournalViewSet, basename='journal')
router.register(r'posts/(?P<post_id>\d+)/comments',
                CommentViewSet, basename='comment')
router.register('follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        'v1/journals/<int:pk>/export/', 
        JournalExportAPIView.as_view(), 
        name='journal-export'
    ),
    path('v1/', include('djoser.urls')),
    path('v1/', include('djoser.urls.jwt')),
]
