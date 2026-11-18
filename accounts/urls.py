from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.register, name='register'), 
    path('verify/', views.verify, name='verify'), 
    path('resend/', views.request_code, {'purpose': 'register'}, name='resend'), 
    path('refresh/', views.refresh),
    path('profile/', views.profile),
    path('login/', views.login_view, name='login'), 
    path('logout/', views.logout_view, name='logout'), 
    path('forgot/', views.request_code, {'purpose': 'reset'}, name='forgot'), 
    path('reset/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password')
]
