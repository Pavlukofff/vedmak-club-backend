"""
URL configuration for vedmak_club project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import ThrottledTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/ranks/", include("apps.ranks.urls")),
    path("api/penalties/", include("apps.penalties.urls")),
    path("api/battles/", include("apps.battles.urls")),
    path("api/bestiary/", include("apps.bestiary.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/shop/", include("apps.shop.urls")),
    path("api/subscriptions/", include("apps.subscriptions.urls")),
    path("api/tournaments/", include("apps.tournaments.urls")),
    path("api/blog/", include("apps.blog.urls")),
    path("api/schedule/", include("apps.schedule.urls")),
    path("api/codex/", include("apps.codex.urls")),
    path("api/social-links/", include("apps.social.urls")),
    path("api/fundraisers/", include("apps.fundraisers.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/titles/", include("apps.titles.urls")),
    path("api/faq/", include("apps.faq.urls")),
    path("api/auth/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
