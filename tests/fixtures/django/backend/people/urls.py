from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('persons', views.PersonViewSet)
urlpatterns = [
    path('submit/', views.PersonView.as_view()),
    re_path(r'^health/$', views.health),
    path('', include(router.urls)),
]
