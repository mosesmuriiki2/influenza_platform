from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import BusinessProfile
from .models_credit import Invoice, Transaction, CreditWallet

class CreditPurchaseForm(forms.Form):
    PAYMENT_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        label='Payment Method'
    )
    
    credits = forms.IntegerField(
        min_value=settings.MINIMUM_CREDIT_PURCHASE,
        max_value=settings.MAXIMUM_CREDIT_PURCHASE,
        label='Number of Credits',
        help_text=f'1 credit = {settings.CREDIT_CONVERSION_RATE} KES',
        validators=[
            MinValueValidator(settings.MINIMUM_CREDIT_PURCHASE),
            MaxValueValidator(settings.MAXIMUM_CREDIT_PURCHASE)
        ]
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        label='M-Pesa Phone Number',
        help_text='Format: 254XXXXXXXXX (without the + sign)'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        phone_number = cleaned_data.get('phone_number')
        
        if payment_method == 'mpesa' and not phone_number:
            self.add_error('phone_number', 'Phone number is required for M-Pesa payments')
        
        return cleaned_data

class BankTransferForm(forms.Form):
    credits = forms.IntegerField(
        min_value=settings.MINIMUM_CREDIT_PURCHASE,
        max_value=settings.MAXIMUM_CREDIT_PURCHASE,
        label='Number of Credits',
        help_text=f'1 credit = {settings.CREDIT_CONVERSION_RATE} KES',
        validators=[
            MinValueValidator(settings.MINIMUM_CREDIT_PURCHASE),
            MaxValueValidator(settings.MAXIMUM_CREDIT_PURCHASE)
        ],
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='Amount (KES)',
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )
    
    reference = forms.CharField(
        max_length=50,
        label='Bank Transfer Reference',
        help_text='Enter the reference number from your bank transfer'
    )
    
    def clean_reference(self):
        reference = self.cleaned_data.get('reference')
        if len(reference) < 5:
            raise forms.ValidationError('Reference number must be at least 5 characters long')
        return reference

class ManualCreditAllocationForm(forms.Form):
    business = forms.ModelChoiceField(
        queryset=BusinessProfile.objects.all(),
        label='Business',
        help_text='Select the business to allocate credits to'
    )
    
    credits = forms.IntegerField(
        min_value=1,
        label='Number of Credits',
        help_text=f'1 credit = {settings.CREDIT_CONVERSION_RATE} KES',
        validators=[MinValueValidator(1)]
    )
    
    reason = forms.CharField(
        max_length=255,
        label='Reason for Allocation',
        help_text='Provide a reason for this manual credit allocation',
        widget=forms.Textarea(attrs={'rows': 3})
    )
    
    generate_invoice = forms.BooleanField(
        required=False,
        initial=True,
        label='Generate Invoice',
        help_text='Generate an invoice for this credit allocation'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        credits = cleaned_data.get('credits')
        
        # Check if master wallet has enough credits
        from .models_credit import MasterWallet
        master_wallet = MasterWallet.get_instance()
        
        if credits and credits > master_wallet.balance:
            self.add_error('credits', f'Not enough credits in master wallet. Available: {master_wallet.balance}')
        
        return cleaned_data


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['business', 'invoice_type', 'amount', 'credits', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default due date to 7 days from now
        if not self.instance.pk:  # Only for new invoices
            self.fields['due_date'].initial = (timezone.now() + timezone.timedelta(days=7)).date()


class InvoiceFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
    ] + Invoice.STATUS_CHOICES
    
    TYPE_CHOICES = [
        ('', 'All Types'),
    ] + Invoice.INVOICE_TYPES
    
    business = forms.ModelChoiceField(
        queryset=BusinessProfile.objects.all(),
        required=False,
        label='Business',
        empty_label='All Businesses'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    
    invoice_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        label='Invoice Type'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Date From'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Date To'
    )