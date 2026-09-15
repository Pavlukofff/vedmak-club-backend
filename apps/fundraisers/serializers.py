from rest_framework import serializers

from apps.accounts.models import User

from .models import Fundraiser, FundraiserContribution


class ContributionSerializer(serializers.ModelSerializer):
    contributor_display = serializers.SerializerMethodField()

    class Meta:
        model = FundraiserContribution
        fields = ["id", "contributor_display", "amount", "comment", "created_at"]

    def get_contributor_display(self, obj):
        if obj.is_anonymous:
            return "Аноним"
        if obj.contributor_id:
            return obj.contributor.display_name
        return obj.contributor_name or "Аноним"


class ContributionCreateSerializer(serializers.ModelSerializer):
    """Раздел 1 плана: фиксация офлайн-взноса — только can_manage_fundraisers."""

    contributor = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = FundraiserContribution
        fields = ["id", "contributor", "contributor_name", "amount", "is_anonymous", "comment"]


class FundraiserSerializer(serializers.ModelSerializer):
    raised_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Fundraiser
        fields = [
            "id", "title", "description", "cover_image", "goal_amount",
            "raised_amount", "progress_percent", "status", "start_date", "end_date",
        ]


class FundraiserDetailSerializer(FundraiserSerializer):
    contributions = serializers.SerializerMethodField()

    class Meta(FundraiserSerializer.Meta):
        fields = FundraiserSerializer.Meta.fields + ["contributions"]

    def get_contributions(self, obj):
        return ContributionSerializer(obj.contributions.all(), many=True).data


class FundraiserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fundraiser
        fields = [
            "id", "title", "description", "cover_image", "goal_amount",
            "status", "start_date", "end_date",
        ]
