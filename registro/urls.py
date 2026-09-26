from django.urls import path
from . import views

urlpatterns=[
    path('', views.registrar, name='registrar'),
    path('lista/', views.lista, name='lista'),
    path("eliminar/<int:id>/", views.eliminar, name="eliminar"),
]