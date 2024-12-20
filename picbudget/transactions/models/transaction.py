from django.db import models
from uuid import uuid4


# Create your models here.
class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]
    INPUT_METHOD = [
        ("manual", "Manual"),
        ("picscan", "PicScan"),
        ("picvoice", "PicVoice"),
    ]
    CONFIRMATION_STATUS = [
        ("confirmed", "Confirmed"),
        ("unconfirmed", "Unconfirmed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(
        "wallets.Wallet", on_delete=models.CASCADE, null=True, blank=True, default=None
    )
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, default="expense")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    labels = models.ManyToManyField(
        "labels.Label", blank=True, related_name="transactions_labels"
    )
    receipt = models.ImageField(upload_to="receipts", blank=True, null=True)
    method = models.CharField(max_length=10, choices=INPUT_METHOD, default="manual")
    status = models.CharField(
        max_length=12, choices=CONFIRMATION_STATUS, default="confirmed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.wallet.user.full_name

    def get_receipt_url(self):
        if self.receipt and hasattr(self.receipt, "url"):
            return self.receipt.url
        return None
