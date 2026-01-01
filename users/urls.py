from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('disponibilidad/', views.gestionar_disponibilidad, name='disponibilidad'),
    path('disponibilidad/resumen/', views.resumen_disponibilidad, name='resumen_disponibilidad'),
    path('mis-programaciones/', views.mis_programaciones, name='mis_programaciones'),
    path('programaciones/', views.lista_programaciones, name='lista_programaciones'),
    path('programaciones/<int:programacion_id>/', views.detalle_programacion, name='detalle_programacion'),
    path('whatsapp-links/<int:programacion_id>/', views.ver_links_whatsapp, name='ver_links_whatsapp'),
]
