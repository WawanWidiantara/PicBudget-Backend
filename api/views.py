import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from rest_framework import generics, permissions
from .models import Wallet, Transaction, TransactionItem
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    UserSerializer,
    TransactionItemSerializer,
    RegisterSerializer,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import models
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import cv2
import numpy as np
from .processors.page_extractor import PageExtractor
from .processors.text_extractor import TextExtractor
from .processors.receipt_processor import ReceiptProcessor
from datetime import datetime
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class WalletListCreateView(generics.ListCreateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WalletListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        wallets = Wallet.objects.filter(user=request.user)
        serializer = WalletSerializer(wallets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TotalAmountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_amount = (
            Wallet.objects.filter(user=request.user).aggregate(
                total=models.Sum("balance")
            )["total"]
            or 0
        )
        return Response({"total_amount": total_amount}, status=status.HTTP_200_OK)


class TotalTransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_transactions = (
            Transaction.objects.filter(wallet__user=request.user).aggregate(
                total=models.Sum("amount")
            )["total"]
            or 0
        )
        return Response(
            {"total_transactions": total_transactions}, status=status.HTTP_200_OK
        )


class WalletDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        wallet = Wallet.objects.get(id=self.request.data["wallet"])
        wallet.balance -= serializer.validated_data["amount"]
        wallet.save()
        serializer.save()

    def get_queryset(self):
        return self.queryset.filter(wallet__user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(wallet__user=self.request.user)


class ExtractTextAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Save the uploaded file temporarily
            file_name = default_storage.save(f"receipts/temp_{file.name}", file)
            file_url = default_storage.url(file_name)

            # Read the file content for processing
            file.seek(0)  # Ensure the file pointer is at the beginning
            file_content = file.read()
            np_img = np.frombuffer(file_content, np.uint8)

            if np_img.size == 0:
                return Response(
                    {"error": "File buffer is empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            original_image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if original_image is None:
                return Response(
                    {"error": "Failed to decode image"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Make a copy of the original image for processing
            image_for_processing = original_image.copy()

            # Process the image
            page_extractor = PageExtractor(
                image_array=image_for_processing, remove_background="n"
            )
            preprocessed_image = page_extractor.preprocess_image()

            preprocessed_image = cv2.cvtColor(preprocessed_image, cv2.COLOR_GRAY2BGR)

            text_extractor = TextExtractor(preprocessed_image)
            extracted_text = text_extractor.extracted_text

            model_path = "api/ner_model_v3"
            processor = ReceiptProcessor(model_path)
            result = processor.process_receipt(extracted_text)
            result["receipt_image_url"] = file_url

            # Return the extracted result for user review
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateTransactionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            wallet_id = request.data.get("wallet")
            if not wallet_id:
                return Response(
                    {"error": "No wallet provided"}, status=status.HTTP_400_BAD_REQUEST
                )

            wallet = Wallet.objects.get(id=wallet_id)

            # Ensure the wallet belongs to the authenticated user
            try:
                wallet = Wallet.objects.get(id=wallet_id, user=request.user)
            except Wallet.DoesNotExist:
                return Response(
                    {"error": "Wallet not found or does not belong to the user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Extract transaction details from the request
            ocr_data = request.data.get("ocr_data")
            amount = ocr_data.get("total")
            location = ocr_data.get("address")
            date = ocr_data.get("date")
            items = ocr_data.get("items")
            receipt_image_url = ocr_data.get("receipt_image_url")

            if not amount or not date or not items:
                return Response(
                    {"error": "Missing transaction details"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create a transaction with the confirmed data
            transaction = Transaction(
                wallet=wallet,
                amount=amount,
                location=location,
                date=datetime.strptime(date, "%d/%m/%Y"),
                receipt_image=receipt_image_url,
                ocr_data=ocr_data,
            )
            transaction.save()

            wallet.balance -= transaction.amount
            wallet.save()

            # Create TransactionItem entries
            for item in items:
                TransactionItem.objects.create(
                    transaction=transaction,
                    item_name=item["item"],
                    item_price=item["price"],
                )

            # Delete the temporary image file after transaction is created
            image_path = os.path.join(
                settings.MEDIA_ROOT, receipt_image_url.lstrip("/")
            )
            if os.path.exists(image_path):
                os.remove(image_path)

            return Response(
                TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )
