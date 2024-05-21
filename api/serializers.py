from rest_framework import serializers
from .models import User, Wallet, Transaction, TransactionItem
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "dob", "gender", "phone_number", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "user", "wallet_name", "balance"]


class TransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionItem
        fields = ["id", "transaction", "item_name", "item_price"]


class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True)

    class Meta:
        model = Transaction
        fields = ["id", "wallet", "amount", "location", "date", "ocr_data", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        transaction = Transaction.objects.create(**validated_data)
        for item_data in items_data:
            TransactionItem.objects.create(transaction=transaction, **item_data)
        return transaction


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password2",
            "name",
            "dob",
            "gender",
            "phone_number",
            "balance",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        balance = validated_data.pop("balance", 0)
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        Wallet.objects.create(user=user, wallet_name="main", balance=balance)
        return user
