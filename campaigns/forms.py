from django import forms
from django.core.exceptions import ValidationError
from accounts.models import InfluencerProfile
from .models import Campaign

class CampaignForm(forms.ModelForm):
    """
    Form for creating and updating campaigns
    """
    class Meta:
        model = Campaign
        fields = ['title', 'description', 'start_date', 'end_date', 
                 'budget', 'target_audience', 'platforms', 'categories', 
                 'requirements', 'compensation']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date")

        return cleaned_data

class CampaignApplicationForm(forms.Form):
    """
    Form for influencers to apply to campaigns
    """
    proposal = forms.CharField(
        widget=forms.Textarea,
        help_text="Explain why you're a good fit for this campaign"
    )
    rate = forms.DecimalField(
        help_text="Your proposed rate for this campaign"
    )
    portfolio_link = forms.URLField(
        required=False,
        help_text="Link to your portfolio or relevant work"
    )

    rate = forms.DecimalField(
        help_text="Your proposed rate for this campaign"
    )

    class Meta:
        model = CampaignApplication
        fields = ['message']
        labels = {
            'message': 'Proposal',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'message': "Explain why you're a good fit for this campaign",
        }

    def clean_rate(self):
        rate = self.cleaned_data.get('rate')
        if rate and rate <= 0:
            raise ValidationError("Rate must be a positive number")
        return rate