from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ContactViewSet, PipelineStageViewSet, TagViewSet, LeadViewSet, NoteViewSet, TaskViewSet, LeadStageViewSet
from .analytics import AnalyticsViewSet
from .users import UserViewSet

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'stages', PipelineStageViewSet, basename='stage')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'lead-stages', LeadStageViewSet, basename='leadstage')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'auth/users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
