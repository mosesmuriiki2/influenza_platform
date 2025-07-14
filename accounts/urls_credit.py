from django.urls import path
from . import views_credit

urlpatterns = [
    # Credit purchase and management
    path('credit/purchase/', views_credit.CreditPurchaseView.as_view(), name='credit_purchase'),
    path('credit/transactions/', views_credit.TransactionHistoryView.as_view(), name='transaction_history'),
    path('credit/receipt/<int:pk>/', views_credit.ReceiptView.as_view(), name='credit_receipt'),
    
    # M-Pesa integration
    path('credit/mpesa/callback/', views_credit.MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('credit/mpesa/status/<str:reference>/', views_credit.MpesaSTKStatusView.as_view(), name='mpesa_status'),
    
    # Bank transfer
    path('credit/bank-transfer/', views_credit.BankTransferView.as_view(), name='bank_transfer'),
    path('credit/bank-transfer/confirm/<int:pk>/', views_credit.BankTransferConfirmView.as_view(), name='bank_transfer_confirm'),
    
    # Admin credit management
    path('admin/credit/dashboard/', views_credit.MasterCreditDashboardView.as_view(), name='master_credit_dashboard'),
    path('admin/credit/business/', views_credit.BusinessCreditManagementView.as_view(), name='business_credit_management'),
    path('admin/credit/business/<int:business_id>/', views_credit.BusinessCreditDetailView.as_view(), name='business_credit_detail'),
    path('admin/credit/reconciliation/', views_credit.ReconciliationView.as_view(), name='credit_reconciliation'),
    path('admin/credit/manual-allocation/', views_credit.ManualCreditAllocationView.as_view(), name='manual_credit_allocation'),
    
    # Invoices and Receipts
    path('invoices/', views_credit.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views_credit.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', views_credit.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('receipts/<int:pk>/pdf/', views_credit.ReceiptPDFView.as_view(), name='receipt_pdf'),
    path('admin/invoices/create/', views_credit.AdminInvoiceCreateView.as_view(), name='admin_invoice_create'),
    path('admin/invoices/<int:pk>/mark-paid/', views_credit.mark_invoice_paid, name='mark_invoice_paid'),
]