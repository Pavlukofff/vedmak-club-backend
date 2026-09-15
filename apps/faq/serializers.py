from rest_framework import serializers

from .models import FAQItem


class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ["id", "question", "answer", "category"]
