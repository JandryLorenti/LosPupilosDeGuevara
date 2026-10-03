from django.urls import path
from . import views


urlpatterns=[
    path('', views.registrar, name='registrar'),
    path('lista/', views.lista, name='lista'),
    path("eliminar/<int:id>/", views.eliminar, name="eliminar"),
    path('editar/<int:id>/', views.editar, name='editar'),
    path('crear-cuenta/', views.registro_usuario, name='registro_usuario')
]