from django.urls import path, include
from rest_framework import routers
from myapp import views

router = routers.DefaultRouter()
router.register(r'pillstation', views.PillStationViewSet)

urlpatterns = [
    path('', include(router.urls))
]