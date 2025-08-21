from django.db import models
from common.models import TimeStampedBaseModel
from django.conf import settings


class Server(TimeStampedBaseModel):
    VISIBILITY_CHOICES = (
        ("public", "Public"),
        ("private", "Private"),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        choices=VISIBILITY_CHOICES, max_length=20, default="public"
    )
    icon = models.ImageField(upload_to="icons/", blank=True, null=True)
    invite_code = models.CharField(max_length=10, blank=True, null=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ServerMembership",
        related_name="joined_servers",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_servers"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure owner automatically becomes a member with role="owner"
        ServerMembership.objects.get_or_create(
            user=self.owner, server=self, defaults={"role": "owner"}
        )

    @property
    def get_member_count(self):
        return self.members.count()


class ServerMembership(TimeStampedBaseModel):
    MEMBERSHIP_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="server_membership",
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name="membership"
    )
    role = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, default="member")

    def __str__(self):
        return f"{self.user.display_name} - {self.server.name}"

    class Meta:
        unique_together = ["user", "server"]
