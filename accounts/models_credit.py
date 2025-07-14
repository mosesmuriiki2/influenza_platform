from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
import uuid
import os
from .models import BusinessProfile, Campaign

class MasterWallet(models.Model):
    """
    Master wallet for the admin to manage all credits in the system.
    This is a singleton model - only one instance should exist.
    """
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Balance in credits (1 credit = 1000 KES)
    credit_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_reconciliation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Master Wallet"
        verbose_name_plural = "Master Wallet"
    
    def __str__(self):
        return f"Master Wallet (Balance: {self.credit_balance} credits / {self.balance} KES)"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and MasterWallet.objects.exists():
            return MasterWallet.objects.first()
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
    
    def reconcile(self):
        """Perform daily reconciliation"""
        # Calculate total credits allocated to businesses
        business_credits = CreditWallet.objects.aggregate(models.Sum('credit_balance'))['credit_balance__sum'] or 0
        
        # Update last reconciliation timestamp
        self.last_reconciliation = timezone.now()
        self.save()
        
        # Create reconciliation record
        Reconciliation.objects.create(
            master_wallet=self,
            total_system_credits=self.credit_balance,
            total_business_credits=business_credits,
            is_balanced=(self.credit_balance == business_credits)
        )
        
        return self.credit_balance == business_credits

class CreditWallet(models.Model):
    """
    Credit wallet for businesses to purchase and use credits for campaigns
    """
    business = models.OneToOneField(BusinessProfile, on_delete=models.CASCADE, related_name='credit_wallet')
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # KES equivalent (1 credit = 1000 KES)
    balance_kes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business.company_name}'s Wallet (Balance: {self.credit_balance} credits)"
    
    def add_credits(self, amount, transaction_type, reference=None):
        """Add credits to the wallet and create a transaction record"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Update wallet balance
        self.credit_balance += amount
        self.balance_kes = self.credit_balance * 1000  # 1 credit = 1000 KES
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=transaction_type,
            reference=reference,
            balance_after=self.credit_balance
        )
        
        return True
    
    def deduct_credits(self, amount, transaction_type, reference=None):
        """Deduct credits from the wallet and create a transaction record"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.credit_balance < amount:
            raise ValueError("Insufficient credits")
        
        # Update wallet balance
        self.credit_balance -= amount
        self.balance_kes = self.credit_balance * 1000  # 1 credit = 1000 KES
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=-amount,  # Negative amount for deduction
            transaction_type=transaction_type,
            reference=reference,
            balance_after=self.credit_balance
        )
        
        return True

class Transaction(models.Model):
    """
    Record of all credit transactions in the system
    """
    wallet = models.ForeignKey(CreditWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Positive for credit, negative for debit")
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    TRANSACTION_TYPES = [
        ('purchase', 'Credit Purchase'),
        ('campaign', 'Campaign Deduction'),
        ('refund', 'Refund'),
        ('adjustment', 'Manual Adjustment'),
        ('transfer', 'Credit Transfer'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Reference ID for the transaction")
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_generated = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} of {abs(self.amount)} credits for {self.wallet.business.company_name}"
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not already generated
        if not self.receipt_number and self.amount > 0:  # Only for credit transactions
            self.receipt_number = f"RCT-{timezone.now().strftime('%Y%m%d')}-{Transaction.objects.count() + 1:04d}"
            self.receipt_generated = True
        
        super().save(*args, **kwargs)
    
    @property
    def amount_kes(self):
        """Return the KES equivalent of the credit amount"""
        return abs(self.amount) * settings.CREDIT_CONVERSION_RATE
    
    def generate_invoice(self, created_by=None):
        """Generate an invoice for this transaction"""
        # Only generate invoices for credit purchases or allocations
        if self.transaction_type not in ['purchase', 'adjustment']:
            return None
        
        # Check if invoice already exists
        from .models_credit import Invoice
        try:
            return self.invoice
        except Invoice.DoesNotExist:
            pass
        
        # Determine invoice type
        invoice_type = 'purchase' if self.transaction_type == 'purchase' else 'allocation'
        
        # Create invoice
        invoice = Invoice.objects.create(
            business=self.wallet.business,
            transaction=self,
            invoice_type=invoice_type,
            amount=self.amount_kes,
            credits=abs(self.amount),
            status='issued',
            created_by=created_by,
            notes=self.description
        )
        
        # If this is a purchase and already paid, mark as paid
        if self.transaction_type == 'purchase':
            invoice.mark_as_paid(self.timestamp.date())
        
        return invoice
    
    def generate_receipt(self):
        """Generate a receipt for this transaction"""
        # Only generate receipts for credit purchases or allocations
        if self.transaction_type not in ['purchase', 'adjustment'] or self.amount <= 0:
            return None
        
        # Check if receipt already exists
        from .models_credit import Receipt
        try:
            return self.receipt
        except Receipt.DoesNotExist:
            pass
        
        # Get or create invoice
        try:
            invoice = self.invoice
        except Invoice.DoesNotExist:
            invoice = self.generate_invoice()
        
        # Create receipt
        receipt = Receipt.objects.create(
            transaction=self,
            invoice=invoice,
            receipt_number=self.receipt_number or f"RCT-{timezone.now().strftime('%Y%m%d')}-{Receipt.objects.count() + 1:04d}"
        )
        
        return receipt

class CampaignCreditLedger(models.Model):
    """
    Record of credits used for each campaign
    """
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='credit_ledger')
    credits_used = models.DecimalField(max_digits=10, decimal_places=2)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaign_ledgers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.campaign.title} - {self.credits_used} credits"

class MpesaPayment(models.Model):
    """
    Record of M-Pesa payments for credit purchases
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='mpesa_payments')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.DecimalField(max_digits=10, decimal_places=2, help_text="Number of credits purchased")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    result_code = models.CharField(max_length=5, blank=True, null=True)
    result_description = models.TextField(blank=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"M-Pesa Payment of KES {self.amount} by {self.business.company_name}"

class BankTransfer(models.Model):
    """
    Record of bank transfers for credit purchases (manually verified)
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='bank_transfers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.DecimalField(max_digits=10, decimal_places=2, help_text="Number of credits purchased")
    reference_number = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, blank=True)
    transfer_date = models.DateField()
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    receipt_image = models.ImageField(upload_to='bank_transfer_receipts/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transfers')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bank Transfer of KES {self.amount} by {self.business.company_name}"
    
    def verify(self, verified_by):
        """Mark the bank transfer as verified and add credits to the business wallet"""
        if self.status != 'pending':
            return False
        
        self.status = 'verified'
        self.verified_by = verified_by
        self.verified_at = timezone.now()
        self.save()
        
        # Add credits to the business wallet
        try:
            wallet = self.business.credit_wallet
            wallet.add_credits(self.credits, 'purchase', f"Bank Transfer: {self.reference_number}")
            
            # Update master wallet
            master_wallet = MasterWallet.get_instance()
            master_wallet.credit_balance -= self.credits
            master_wallet.balance -= (self.credits * 1000)  # 1 credit = 1000 KES
            master_wallet.save()
            
            return True
        except Exception as e:
            # Revert status if credit addition fails
            self.status = 'pending'
            self.verified_by = None
            self.verified_at = None
            self.save()
            raise e

class Reconciliation(models.Model):
    """
    Daily reconciliation records for auditing
    """
    master_wallet = models.ForeignKey(MasterWallet, on_delete=models.CASCADE, related_name='reconciliations')
    date = models.DateField(auto_now_add=True)
    total_system_credits = models.DecimalField(max_digits=12, decimal_places=2)
    total_business_credits = models.DecimalField(max_digits=12, decimal_places=2)
    is_balanced = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        status = "Balanced" if self.is_balanced else "Unbalanced"
        return f"Reconciliation on {self.date} - {status}"


def invoice_file_path(instance, filename):
    """Generate file path for invoice PDFs"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('invoices', filename)


def receipt_file_path(instance, filename):
    """Generate file path for receipt PDFs"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('receipts', filename)


class Invoice(models.Model):
    """
    Invoice model for credit purchases and allocations
    """
    INVOICE_TYPES = [
        ('purchase', 'Credit Purchase'),
        ('allocation', 'Credit Allocation'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='invoices')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='invoice', null=True, blank=True)
    mpesa_payment = models.OneToOneField(MpesaPayment, on_delete=models.SET_NULL, related_name='invoice', null=True, blank=True)
    bank_transfer = models.OneToOneField(BankTransfer, on_delete=models.SET_NULL, related_name='invoice', null=True, blank=True)
    
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.DecimalField(max_digits=10, decimal_places=2)
    
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # PDF file of the generated invoice
    pdf_file = models.FileField(upload_to=invoice_file_path, null=True, blank=True)
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.business.company_name}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not already set
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{Invoice.objects.count() + 1:04d}"
        
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, paid_date=None):
        """Mark the invoice as paid"""
        self.status = 'paid'
        self.paid_date = paid_date or timezone.now().date()
        self.save()


class Receipt(models.Model):
    """
    Receipt model for completed transactions
    """
    receipt_number = models.CharField(max_length=50, unique=True)
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='receipt', null=True, blank=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='receipt')
    
    issued_date = models.DateField(auto_now_add=True)
    
    # PDF file of the generated receipt
    pdf_file = models.FileField(upload_to=receipt_file_path, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.transaction.wallet.business.company_name}"
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not already set
        if not self.receipt_number:
            self.receipt_number = f"RCT-{timezone.now().strftime('%Y%m%d')}-{Receipt.objects.count() + 1:04d}"
        
        super().save(*args, **kwargs)