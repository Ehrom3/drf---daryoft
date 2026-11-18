from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.items),
    path('items/<int:pk>/', views.detail),
    path('items/<int:pk>/responses/', views.replies),
    path('my-items/', views.my_items),
    path('my-responses/', views.my_responses),
    path('categories/', views.categories),
    path('cities/', views.cities),
]
