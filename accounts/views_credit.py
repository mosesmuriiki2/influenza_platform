from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView, FormView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from .decorators import admin_required
import json
import uuid
import datetime
import base64
import requests
import io
import os
from decimal import Decimal
from weasyprint import HTML, CSS

from .models import User, BusinessProfile
from .models_credit import (
    MasterWallet, CreditWallet, Transaction, 
    CampaignCreditLedger, MpesaPayment, BankTransfer, Reconciliation,
    Invoice, Receipt
)
from .mpesa_api import MpesaClient, process_stk_callback
from .forms_credit import (
    CreditPurchaseForm, BankTransferForm, ManualCreditAllocationForm,
    InvoiceForm, InvoiceFilterForm
)

# Helper function to check if user is a business
def is_business_user(user):
    return user.is_authenticated and user.user_type == 'business'

# Helper function to check if user is an admin
def is_admin_user(user):
    return user.is_authenticated and user.user_type == 'admin'

# Business user views
class CreditPurchaseView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'accounts/credit_purchase.html'
    form_class = CreditPurchaseForm
    success_url = reverse_lazy('credit_history')
    
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            wallet = CreditWallet.objects.get(business__user=self.request.user)
            context['wallet'] = wallet
            context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
            context['min_credits'] = settings.MINIMUM_CREDIT_PURCHASE
            context['max_credits'] = settings.MAXIMUM_CREDIT_PURCHASE
        except CreditWallet.DoesNotExist:
            # Create wallet if it doesn't exist
            business = BusinessProfile.objects.get(user=self.request.user)
            wallet = CreditWallet.objects.create(business=business, balance=0)
            context['wallet'] = wallet
        return context
    
    def form_valid(self, form):
        payment_method = form.cleaned_data['payment_method']
        credits = form.cleaned_data['credits']
        amount_kes = credits * settings.CREDIT_CONVERSION_RATE
        
        # Get or create wallet
        business = BusinessProfile.objects.get(user=self.request.user)
        wallet, created = CreditWallet.objects.get_or_create(
            business=business,
            defaults={'balance': 0}
        )
        
        if payment_method == 'mpesa':
            # Process M-Pesa payment
            phone_number = form.cleaned_data['phone_number']
            
            # Initialize M-Pesa client
            mpesa_client = MpesaClient()
            
            # Initiate STK push
            response = mpesa_client.stk_push(
                phone_number=phone_number,
                amount=amount_kes,
                account_reference=f"INFL-{business.id}",
                transaction_desc=f"Credit Purchase: {credits} credits"
            )
            
            if 'CheckoutRequestID' in response:
                # Create pending M-Pesa payment record
                mpesa_payment = MpesaPayment.objects.create(
                    business=business,
                    amount=amount_kes,
                    phone_number=phone_number,
                    checkout_request_id=response['CheckoutRequestID'],
                    credits=credits,
                    status='pending'
                )
                
                # Redirect to status page
                return JsonResponse({
                    'success': True,
                    'message': 'Please complete the payment on your phone',
                    'checkout_request_id': response['CheckoutRequestID']
                })
            else:
                # Handle error
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to initiate M-Pesa payment. Please try again.'
                })
        
        elif payment_method == 'bank':
            # Redirect to bank transfer page
            return redirect(reverse('bank_transfer') + f'?credits={credits}')
        
        return super().form_valid(form)

class TransactionHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'accounts/transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get_queryset(self):
        business = BusinessProfile.objects.get(user=self.request.user)
        return Transaction.objects.filter(wallet__business=business).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = BusinessProfile.objects.get(user=self.request.user)
        wallet, created = CreditWallet.objects.get_or_create(
            business=business,
            defaults={'balance': 0}
        )
        context['wallet'] = wallet
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        return context

class ReceiptView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'accounts/credit_receipt.html'
    context_object_name = 'transaction'
    
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get_queryset(self):
        business = BusinessProfile.objects.get(user=self.request.user)
        return Transaction.objects.filter(wallet__business=business)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['business'] = BusinessProfile.objects.get(user=self.request.user)
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        return context

class BankTransferView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'accounts/bank_transfer.html'
    form_class = BankTransferForm
    success_url = reverse_lazy('credit_history')
    
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get_initial(self):
        initial = super().get_initial()
        credits = self.request.GET.get('credits', 1)
        try:
            credits = int(credits)
            if credits < settings.MINIMUM_CREDIT_PURCHASE:
                credits = settings.MINIMUM_CREDIT_PURCHASE
            elif credits > settings.MAXIMUM_CREDIT_PURCHASE:
                credits = settings.MAXIMUM_CREDIT_PURCHASE
        except ValueError:
            credits = settings.MINIMUM_CREDIT_PURCHASE
            
        initial['credits'] = credits
        initial['amount'] = credits * settings.CREDIT_CONVERSION_RATE
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        return context
    
    def form_valid(self, form):
        business = BusinessProfile.objects.get(user=self.request.user)
        credits = form.cleaned_data['credits']
        amount = credits * settings.CREDIT_CONVERSION_RATE
        reference = form.cleaned_data['reference']
        
        # Create bank transfer record
        bank_transfer = BankTransfer.objects.create(
            business=business,
            amount=amount,
            reference=reference,
            credits=credits,
            status='pending'
        )
        
        messages.success(
            self.request,
            'Bank transfer information submitted successfully. Credits will be added to your account once payment is verified.'
        )
        return super().form_valid(form)

class BankTransferConfirmView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'accounts/bank_transfer_confirm.html'
    
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = BusinessProfile.objects.get(user=self.request.user)
        context['pending_transfers'] = BankTransfer.objects.filter(
            business=business,
            status='pending'
        ).order_by('-created_at')
        return context

# M-Pesa integration views
@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(View):
    def post(self, request, *args, **kwargs):
        # Process the callback data
        data = json.loads(request.body)
        process_stk_callback(data)
        return HttpResponse(status=200)

class MpesaSTKStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_business_user(self.request.user)
    
    def get(self, request, checkout_request_id, *args, **kwargs):
        try:
            mpesa_payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)
            
            # If still pending, check status
            if mpesa_payment.status == 'pending':
                mpesa_client = MpesaClient()
                response = mpesa_client.check_stk_status(checkout_request_id)
                
                if 'ResultCode' in response and response['ResultCode'] == 0:
                    # Payment successful, update status
                    mpesa_payment.status = 'completed'
                    mpesa_payment.save()
                    
                    # Add credits to wallet
                    with transaction.atomic():
                        # Get master wallet
                        master_wallet = MasterWallet.get_instance()
                        
                        # Get business wallet
                        business_wallet, created = CreditWallet.objects.get_or_create(
                            business=mpesa_payment.business,
                            defaults={'balance': 0}
                        )
                        
                        # Add credits to business wallet
                        business_wallet.add_credits(mpesa_payment.credits)
                        
                        # Deduct credits from master wallet
                        master_wallet.deduct_credits(mpesa_payment.credits)
                        
                        # Create transaction record
                        Transaction.objects.create(
                            wallet=business_wallet,
                            amount=mpesa_payment.credits,
                            transaction_type='purchase',
                            reference=f"M-Pesa: {mpesa_payment.mpesa_receipt_number}",
                            description=f"Credit purchase via M-Pesa"
                        )
                    
                    return JsonResponse({
                        'success': True,
                        'status': 'completed',
                        'message': f'Payment successful. {mpesa_payment.credits} credits added to your account.'
                    })
                elif 'ResultCode' in response and response['ResultCode'] != 0:
                    # Payment failed
                    mpesa_payment.status = 'failed'
                    mpesa_payment.save()
                    return JsonResponse({
                        'success': False,
                        'status': 'failed',
                        'message': 'Payment failed. Please try again.'
                    })
                else:
                    # Still pending
                    return JsonResponse({
                        'success': True,
                        'status': 'pending',
                        'message': 'Payment is being processed. Please wait.'
                    })
            else:
                # Return current status
                return JsonResponse({
                    'success': True,
                    'status': mpesa_payment.status,
                    'message': f'Payment {mpesa_payment.status}.'
                })
        except MpesaPayment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid payment reference.'
            }, status=404)

# Admin views
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin_user(self.request.user)

class MasterCreditDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'accounts/admin/master_credit_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get master wallet
        master_wallet = MasterWallet.get_instance()
        context['master_wallet'] = master_wallet
        
        # Get total credits allocated to businesses
        total_allocated = CreditWallet.objects.aggregate(total=Sum('balance'))['total'] or 0
        context['total_allocated'] = total_allocated
        
        # Calculate available float
        context['available_float'] = master_wallet.balance - total_allocated
        
        # Get recent transactions
        context['recent_transactions'] = Transaction.objects.order_by('-timestamp')[:10]
        
        # Get credit conversion rate
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        
        return context

class BusinessCreditManagementView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    template_name = 'accounts/admin/business_credit_management.html'
    context_object_name = 'business'
    model = BusinessProfile
    pk_url_kwarg = 'business_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_object()
        
        # Get business wallet
        wallet, created = CreditWallet.objects.get_or_create(
            business=business,
            defaults={'balance': 0}
        )
        context['wallet'] = wallet
        
        # Get transactions
        context['transactions'] = Transaction.objects.filter(
            wallet=wallet
        ).order_by('-timestamp')
        
        # Get pending bank transfers
        context['pending_transfers'] = BankTransfer.objects.filter(
            business=business,
            status='pending'
        ).order_by('-created_at')
        
        # Get credit conversion rate
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        
        return context
    
    def post(self, request, *args, **kwargs):
        business = self.get_object()
        action = request.POST.get('action')
        
        if action == 'verify_bank_transfer':
            transfer_id = request.POST.get('transfer_id')
            transfer = get_object_or_404(BankTransfer, id=transfer_id, business=business)
            
            # Verify transfer
            transfer.status = 'completed'
            transfer.verified_by = request.user
            transfer.verified_at = timezone.now()
            transfer.save()
            
            # Add credits to wallet
            with transaction.atomic():
                # Get master wallet
                master_wallet = MasterWallet.get_instance()
                
                # Get business wallet
                business_wallet, created = CreditWallet.objects.get_or_create(
                    business=business,
                    defaults={'balance': 0}
                )
                
                # Add credits to business wallet
                business_wallet.add_credits(transfer.credits)
                
                # Deduct credits from master wallet
                master_wallet.deduct_credits(transfer.credits)
                
                # Create transaction record
                Transaction.objects.create(
                    wallet=business_wallet,
                    amount=transfer.credits,
                    transaction_type='purchase',
                    reference=f"Bank Transfer: {transfer.reference}",
                    description=f"Credit purchase via bank transfer"
                )
            
            messages.success(request, f'Bank transfer verified and {transfer.credits} credits added to {business.company_name}')
        
        return redirect('business_credit_management', business_id=business.id)

class ReconciliationView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'accounts/admin/reconciliation.html'
    context_object_name = 'reconciliations'
    model = Reconciliation
    paginate_by = 10
    ordering = ['-date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get master wallet
        master_wallet = MasterWallet.get_instance()
        context['master_wallet'] = master_wallet
        
        # Get total credits allocated to businesses
        total_allocated = CreditWallet.objects.aggregate(total=Sum('balance'))['total'] or 0
        context['total_allocated'] = total_allocated
        
        # Calculate available float
        context['available_float'] = master_wallet.balance - total_allocated
        
        # Get credit conversion rate
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        
        return context
    
    def post(self, request, *args, **kwargs):
        if 'reconcile' in request.POST:
            # Perform reconciliation
            master_wallet = MasterWallet.get_instance()
            total_allocated = CreditWallet.objects.aggregate(total=Sum('balance'))['total'] or 0
            available_float = master_wallet.balance - total_allocated
            
            # Create reconciliation record
            reconciliation = Reconciliation.objects.create(
                master_balance=master_wallet.balance,
                total_allocated=total_allocated,
                available_float=available_float,
                performed_by=request.user
            )
            
            messages.success(request, 'Reconciliation completed successfully.')
            
        return redirect('credit_reconciliation')

class ManualCreditAllocationView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    template_name = 'accounts/admin/manual_credit_allocation.html'
    form_class = ManualCreditAllocationForm
    success_url = reverse_lazy('master_credit_dashboard')
    
    def form_valid(self, form):
        business = form.cleaned_data['business']
        credits = form.cleaned_data['credits']
        reason = form.cleaned_data['reason']
        generate_invoice = form.cleaned_data.get('generate_invoice', True)
        
        # Add credits to wallet
        with transaction.atomic():
            # Get master wallet
            master_wallet = MasterWallet.get_instance()
            
            # Get business wallet
            business_wallet, created = CreditWallet.objects.get_or_create(
                business=business,
                defaults={'balance': 0}
            )
            
            # Add credits to business wallet
            business_wallet.add_credits(credits)
            
            # Deduct credits from master wallet
            master_wallet.deduct_credits(credits)
            
            # Create transaction record
            transaction = Transaction.objects.create(
                wallet=business_wallet,
                amount=credits,
                transaction_type='allocation',
                reference=f"Manual Allocation by {self.request.user.email}",
                description=reason
            )
            
            # Generate invoice if requested
            if generate_invoice:
                invoice = transaction.generate_invoice(created_by=self.request.user)
                if invoice:
                    # Generate PDF for the invoice
                    self.generate_invoice_pdf(invoice)
                    messages.success(self.request, f'Invoice #{invoice.invoice_number} generated for {business.company_name}')
        
        messages.success(self.request, f'{credits} credits allocated to {business.company_name} successfully.')
        return super().form_valid(form)
    
    def generate_invoice_pdf(self, invoice):
        """Generate PDF for the invoice"""
        # Render the invoice template to HTML
        context = {
            'invoice': invoice,
            'business': invoice.business,
            'credit_value_kes': settings.CREDIT_CONVERSION_RATE
        }
        html_string = render_to_string('accounts/invoice_pdf.html', context)
        
        # Generate PDF from HTML
        html = HTML(string=html_string, base_url=self.request.build_absolute_uri('/'))
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        
        # Save the PDF to the invoice model
        pdf_file.seek(0)
        invoice.pdf_file.save(f"invoice_{invoice.invoice_number}.pdf", ContentFile(pdf_file.read()), save=True)


class InvoiceListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter based on user type
        if is_admin_user(self.request.user):
            queryset = Invoice.objects.all()
        elif is_business_user(self.request.user):
            business = BusinessProfile.objects.get(user=self.request.user)
            queryset = Invoice.objects.filter(business=business)
        else:
            queryset = Invoice.objects.none()
        
        # Apply filters from form
        form = InvoiceFilterForm(self.request.GET)
        if form.is_valid():
            filters = {}
            
            if form.cleaned_data.get('business'):
                filters['business'] = form.cleaned_data['business']
            
            if form.cleaned_data.get('status'):
                filters['status'] = form.cleaned_data['status']
            
            if form.cleaned_data.get('invoice_type'):
                filters['invoice_type'] = form.cleaned_data['invoice_type']
            
            if form.cleaned_data.get('date_from'):
                filters['issued_date__gte'] = form.cleaned_data['date_from']
            
            if form.cleaned_data.get('date_to'):
                filters['issued_date__lte'] = form.cleaned_data['date_to']
            
            queryset = queryset.filter(**filters)
        
        return queryset.order_by('-issued_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = InvoiceFilterForm(self.request.GET)
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    template_name = 'accounts/invoice_detail.html'
    context_object_name = 'invoice'
    model = Invoice
    
    def get_queryset(self):
        # Filter based on user type
        if is_admin_user(self.request.user):
            return Invoice.objects.all()
        elif is_business_user(self.request.user):
            business = BusinessProfile.objects.get(user=self.request.user)
            return Invoice.objects.filter(business=business)
        return Invoice.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['credit_value_kes'] = settings.CREDIT_CONVERSION_RATE
        return context


class InvoicePDFView(LoginRequiredMixin, DetailView):
    model = Invoice
    
    def get_queryset(self):
        # Filter based on user type
        if is_admin_user(self.request.user):
            return Invoice.objects.all()
        elif is_business_user(self.request.user):
            business = BusinessProfile.objects.get(user=self.request.user)
            return Invoice.objects.filter(business=business)
        return Invoice.objects.none()
    
    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        
        # Check if PDF already exists
        if invoice.pdf_file and os.path.exists(invoice.pdf_file.path):
            return FileResponse(open(invoice.pdf_file.path, 'rb'), content_type='application/pdf')
        
        # Generate PDF if it doesn't exist
        context = {
            'invoice': invoice,
            'business': invoice.business,
            'credit_value_kes': settings.CREDIT_CONVERSION_RATE
        }
        html_string = render_to_string('accounts/invoice_pdf.html', context)
        
        # Generate PDF from HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        
        # Save the PDF to the invoice model
        pdf_file.seek(0)
        invoice.pdf_file.save(f"invoice_{invoice.invoice_number}.pdf", ContentFile(pdf_file.read()), save=True)
        
        # Return the PDF as a response
        pdf_file.seek(0)
        return FileResponse(pdf_file, content_type='application/pdf')


class ReceiptPDFView(LoginRequiredMixin, DetailView):
    model = Receipt
    
    def get_queryset(self):
        # Filter based on user type
        if is_admin_user(self.request.user):
            return Receipt.objects.all()
        elif is_business_user(self.request.user):
            business = BusinessProfile.objects.get(user=self.request.user)
            return Receipt.objects.filter(transaction__wallet__business=business)
        return Receipt.objects.none()
    
    def get(self, request, *args, **kwargs):
        receipt = self.get_object()
        
        # Check if PDF already exists
        if receipt.pdf_file and os.path.exists(receipt.pdf_file.path):
            return FileResponse(open(receipt.pdf_file.path, 'rb'), content_type='application/pdf')
        
        # Generate PDF if it doesn't exist
        context = {
            'receipt': receipt,
            'transaction': receipt.transaction,
            'business': receipt.transaction.wallet.business,
            'credit_value_kes': settings.CREDIT_CONVERSION_RATE
        }
        html_string = render_to_string('accounts/receipt_pdf.html', context)
        
        # Generate PDF from HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        
        # Save the PDF to the receipt model
        pdf_file.seek(0)
        receipt.pdf_file.save(f"receipt_{receipt.receipt_number}.pdf", ContentFile(pdf_file.read()), save=True)
        
        # Return the PDF as a response
        pdf_file.seek(0)
        return FileResponse(pdf_file, content_type='application/pdf')


class AdminInvoiceCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    template_name = 'accounts/admin/invoice_create.html'
    form_class = InvoiceForm
    model = Invoice
    
    def get_success_url(self):
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = 'issued'
        response = super().form_valid(form)
        
        # Generate PDF for the invoice
        self.generate_invoice_pdf(self.object)
        
        messages.success(self.request, f'Invoice #{self.object.invoice_number} created successfully')
        return response
    
    def generate_invoice_pdf(self, invoice):
        """Generate PDF for the invoice"""
        # Render the invoice template to HTML
        context = {
            'invoice': invoice,
            'business': invoice.business,
            'credit_value_kes': settings.CREDIT_CONVERSION_RATE
        }
        html_string = render_to_string('accounts/invoice_pdf.html', context)
        
        # Generate PDF from HTML
        html = HTML(string=html_string, base_url=self.request.build_absolute_uri('/'))
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        
        # Save the PDF to the invoice model
        pdf_file.seek(0)
        invoice.pdf_file.save(f"invoice_{invoice.invoice_number}.pdf", ContentFile(pdf_file.read()), save=True)


@login_required
@admin_required
def mark_invoice_paid(request, pk):
    """Mark an invoice as paid and generate a receipt"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid':
        messages.info(request, f'Invoice #{invoice.invoice_number} is already marked as paid.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    # Mark invoice as paid
    invoice.status = 'paid'
    invoice.paid_date = timezone.now()
    invoice.save()
    
    # If this invoice is associated with a transaction, generate a receipt
    if invoice.transaction:
        receipt = invoice.transaction.generate_receipt()
        if receipt:
            messages.success(request, f'Invoice #{invoice.invoice_number} marked as paid and receipt #{receipt.receipt_number} generated.')
        else:
            messages.success(request, f'Invoice #{invoice.invoice_number} marked as paid.')
    else:
        messages.success(request, f'Invoice #{invoice.invoice_number} marked as paid.')
    
    return redirect('invoice_detail', pk=invoice.pk)