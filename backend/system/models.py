from django.db import models

# Create your models here.
class Radacct(models.Model):
    radacctid = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64)
    acctstarttime = models.DateTimeField(blank=True, null=True)
    acctstoptime = models.DateTimeField(blank=True, null=True)
    acctinterval = models.IntegerField(blank=True, null=True)
    acctsessiontime = models.PositiveIntegerField(blank=True, null=True)
    calledstationid = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'radacct'


class Radcheck(models.Model):
    username = models.CharField(max_length=64)
    value = models.CharField(max_length=253)

    class Meta:
        managed = False
        db_table = 'radcheck'

class Radpostauth(models.Model):
    username = models.CharField(max_length=64)
    pass_field = models.CharField(db_column='pass', max_length=64)  # Field renamed because it was a Python reserved word.
    reply = models.CharField(max_length=32)
    authdate = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'radpostauth'

class Userinfo(models.Model):
    username = models.CharField(max_length=128, blank=True, null=True)
    firstname = models.CharField(max_length=200, blank=True, null=True)
    lastname = models.CharField(max_length=200, blank=True, null=True)
    cpf = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userinfo'