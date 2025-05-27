from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message here...'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Enter message subject...'})
        }