from rest_framework import serializers
from django.db.models import Sum
from picbudget.labels.serializers.label import LabelSerializer
from picbudget.wallets.serializers.wallet import WalletSerializer
from picbudget.picplan.models import Plan
from picbudget.transactions.models import Transaction
from datetime import timedelta
import calendar


class PlanSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    wallets = WalletSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    is_overspent = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "user": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "is_overspent": {"read_only": True},
        }

    def get_progress(self, obj):
        return obj.calculate_progress()

    def get_is_overspent(self, obj):
        return obj.is_overspent()

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

class PlanListSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    is_overspent = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ["id", "name", "amount", "progress", "is_overspent"]

    def get_progress(self, obj):
        return obj.calculate_progress()

    def get_is_overspent(self, obj):
        return obj.is_overspent()

class PlanDetailSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    daily_average = serializers.SerializerMethodField()
    daily_recommended = serializers.SerializerMethodField()
    last_periods = serializers.SerializerMethodField()
    spending_by_labels = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "amount",
            "period",
            "notify_overspent",
            "progress",
            "remaining",
            "daily_average",
            "daily_recommended",
            "last_periods",
            "spending_by_labels",
            "labels",
            "wallets",
        ]

    def get_progress(self, obj):
        return obj.calculate_progress()

    def get_remaining(self, obj):
        progress = obj.calculate_progress()
        total_spent = (progress / 100) * obj.amount if progress else 0
        return round(obj.amount - total_spent, 2)

    def get_daily_average(self, obj):
        transactions = Transaction.objects.filter(
            wallet__in=obj.wallets.all(),
            labels__in=obj.labels.all(),
            transaction_date__month=obj.created_at.month,
        )
        total_spent = transactions.aggregate(total=Sum("amount"))["total"] or 0
        current_day = obj.created_at.day
        if current_day > 0:
            return round(total_spent / current_day, 2)
        return 0

    def get_daily_recommended(self, obj):
        year = obj.created_at.year
        month = obj.created_at.month
        days_in_month = calendar.monthrange(year, month)[1]  # Get the number of days in the month

        if days_in_month > 0:
            return round(obj.amount / days_in_month, 2)
        return 0

    def get_last_periods(self, obj):
        periods = []
        for month_offset in range(1, 5):  # Adjust the range as needed
            previous_month = (obj.created_at - timedelta(days=month_offset * 30)).month
            transactions = Transaction.objects.filter(
                wallet__in=obj.wallets.all(),
                labels__in=obj.labels.all(),
                transaction_date__month=previous_month,
            )
            total_spent = transactions.aggregate(total=Sum("amount"))["total"] or 0
            periods.append(
                {
                    "month": previous_month,
                    "spent": total_spent,
                    "status": "in_limit" if total_spent <= obj.amount else "over_limit",
                }
            )
        return periods

    def get_spending_by_labels(self, obj):
        labels = obj.labels.all()
        data = []
        for label in labels:
            transactions = Transaction.objects.filter(
                labels=label,
                wallet__in=obj.wallets.all(),
                transaction_date__month=obj.created_at.month,
            )
            total_spent = transactions.aggregate(total=Sum("amount"))["total"] or 0
            data.append({"label": label.name, "spent": round(total_spent, 2)})
        return data
