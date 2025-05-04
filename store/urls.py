from store.views import (
    SiteSettingsAPIView,
)

urlpatterns = [
    path("api/v1/site-settings/", SiteSettingsAPIView.as_view(), name="site-settings"),
] 