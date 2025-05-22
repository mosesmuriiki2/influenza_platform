from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Message
from .forms import MessageForm

@login_required
def inbox(request):
    """View for displaying user's inbox messages"""
    user_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = user_messages.filter(read=False).count()
    
    return render(request, 'messaging/inbox.html', {
        'messages_list': user_messages,
        'unread_count': unread_count,
    })

@login_required
def sent_messages(request):
    """View for displaying user's sent messages"""
    sent = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    return render(request, 'messaging/sent.html', {
        'messages_list': sent,
    })

@login_required
def view_message(request, message_id):
    """View for displaying a single message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is either the sender or recipient
    if request.user != message.sender and request.user != message.recipient:
        messages.error(request, "You don't have permission to view this message.")
        return redirect('messages_inbox')
    
    # Mark as read if user is recipient
    if request.user == message.recipient and not message.read:
        message.read = True
        message.save()
    
    return render(request, 'messaging/view_message.html', {
        'message': message,
    })

@login_required
def compose(request):
    """View for composing a new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, "Message sent successfully!")
            return redirect('messages_inbox')
    else:
        # Pre-fill recipient if provided in URL
        recipient_id = request.GET.get('recipient')
        initial_data = {}
        if recipient_id:
            initial_data['recipient'] = recipient_id
        form = MessageForm(initial=initial_data)
    
    return render(request, 'messaging/compose.html', {
        'form': form,
    })

@login_required
def reply(request, message_id):
    """View for replying to a message"""
    original_message = get_object_or_404(Message, id=message_id)
    
    # Check if user is either the sender or recipient
    if request.user != original_message.sender and request.user != original_message.recipient:
        messages.error(request, "You don't have permission to reply to this message.")
        return redirect('messages_inbox')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.subject = f"Re: {original_message.subject}" if original_message.subject else "Re: No Subject"
            message.save()
            messages.success(request, "Reply sent successfully!")
            return redirect('messages_inbox')
    else:
        # Pre-fill the form with the original message's sender as recipient
        recipient = original_message.sender if request.user == original_message.recipient else original_message.recipient
        form = MessageForm(initial={
            'recipient': recipient.id,
            'subject': f"Re: {original_message.subject}" if original_message.subject else "Re: No Subject",
        })
    
    return render(request, 'messaging/compose.html', {
        'form': form,
        'original_message': original_message,
        'is_reply': True,
    })