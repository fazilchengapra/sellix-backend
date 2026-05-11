from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    revenue = serializers.FloatField()
    orders = serializers.IntegerField()
    products = serializers.IntegerField()
    users = serializers.IntegerField()
