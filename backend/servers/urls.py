from django.urls import path
from .views import (
    ServerListView,
    ServerDetailView,
    ServerMembershipListView,
    ServerMembershipDetailView,
)

urlpatterns = [
    path("", ServerListView.as_view(), name="server-list"),
    path("<uuid:pk>/", ServerDetailView.as_view(), name="server-detail"),
    path(
        "<uuid:server_id>/memberships/",
        ServerMembershipListView.as_view(),
        name="server-memberships",
    ),
    path(
        "<uuid:server_id>/members/<uuid:user_id>/",
        ServerMembershipDetailView.as_view(),
        name="server-membership-detail",
    ),
]
