from django.urls import path

from . import views

urlpatterns = [
    path("", views.FAQItemListView.as_view(), name="faq-list"),
    path("<int:pk>/", views.FAQItemDetailView.as_view(), name="faq-detail"),
]
