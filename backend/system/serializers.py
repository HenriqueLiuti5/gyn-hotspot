from rest_framework import serializers
from .models import Radacct, Radcheck, Radpostauth, Userinfo


class RadacctSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Radacct
        fields = [
            'radacctid', 'username', 'acctstarttime', 'acctstoptime',
            'acctsessiontime', 'acctinterval', 'calledstationid',
            'duration_seconds',
        ]

    def get_duration_seconds(self, obj):
        from django.utils import timezone
        if obj.acctstarttime and not obj.acctstoptime:
            return int((timezone.now() - obj.acctstarttime).total_seconds())
        return obj.acctsessiontime


class RadpostAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Radpostauth
        fields = ['id', 'username', 'pass_field', 'reply', 'authdate']


class UserinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userinfo
        fields = ['id', 'username', 'firstname', 'lastname', 'cpf']


class RegisteredUserSerializer(serializers.Serializer):
    
    username = serializers.CharField()
    firstname = serializers.CharField(allow_null=True)
    lastname = serializers.CharField(allow_null=True)
    cpf = serializers.CharField(allow_null=True)
    has_password = serializers.BooleanField()


class DashboardSerializer(serializers.Serializer):
    active_sessions = serializers.IntegerField()
    total_users = serializers.IntegerField()
    auth_attempts_today = serializers.IntegerField()
    auth_success_today = serializers.IntegerField()
    auth_failure_today = serializers.IntegerField()