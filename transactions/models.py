
from django.db import models


class ClientTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.IntegerField(blank=True, null=True)
    journal_id = models.IntegerField(blank=True, null=True)
    account_id = models.IntegerField(blank=True, null=True)
    contact_id = models.IntegerField(blank=True, null=True)
    tax_rate_id = models.IntegerField(blank=True, null=True)
    source_id = models.IntegerField(blank=True, null=True)

    source = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    journal_number = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    journal_reference = models.CharField(max_length=255, blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_rate = models.DecimalField(max_digits=18, decimal_places=6, blank=True, null=True)

    net_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    gross_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)

    transaction_date = models.DateField(blank=True, null=True)
    issued_date = models.DateField(blank=True, null=True)
    created_datetime = models.DateTimeField(blank=True, null=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    sync_timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False                 # جدول جدید نسازه
        db_table = 'client_transaction' # اسم جدول واقعی در MySQL

    def __str__(self):
        return f"{self.id} - {self.description or ''}"
