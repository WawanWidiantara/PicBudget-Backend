from django.urls import path

from .views import (
    UserCreateView,
    WalletListCreateView,
    WalletDetailView,
    TransactionListCreateView,
    TransactionDetailView,
    ExtractTextAPIView,
    CreateTransactionAPIView,
    RegisterView,
    LoginView,
    WalletListView,
    TotalAmountView,
    TotalTransactionsView,
)

urlpatterns = [
    path("users/", UserCreateView.as_view(), name="user-create"),
    path("wallets/", WalletListCreateView.as_view(), name="wallet-list-create"),
    path("wallets/<int:pk>/", WalletDetailView.as_view(), name="wallet-detail"),
    path("users-wallets/", WalletListView.as_view(), name="wallet_list"),
    path("total_amount/", TotalAmountView.as_view(), name="total_amount"),
    path(
        "total_transactions/",
        TotalTransactionsView.as_view(),
        name="total_transactions",
    ),
    path(
        "transactions/",
        TransactionListCreateView.as_view(),
        name="transaction-list-create",
    ),
    path(
        "transactions/<int:pk>/",
        TransactionDetailView.as_view(),
        name="transaction-detail",
    ),
    path("extract/", ExtractTextAPIView.as_view(), name="extract-text"),
    path(
        "create_transaction/",
        CreateTransactionAPIView.as_view(),
        name="create-transaction",
    ),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
]
