import requests
import base64
import json
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class MpesaClient:
    """Client for interacting with the Safaricom M-Pesa Daraja API"""
    
    # API endpoints
    ACCESS_TOKEN_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    STK_PUSH_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    QUERY_STK_STATUS_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    
    # Replace with production URLs when going live
    # ACCESS_TOKEN_URL = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    # STK_PUSH_URL = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    # QUERY_STK_STATUS_URL = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    
    def __init__(self):
        # These should be set in settings.py
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        
        # Check if required settings are configured
        if not all([self.consumer_key, self.consumer_secret, self.business_shortcode, self.passkey, self.callback_url]):
            logger.error("M-Pesa API credentials not fully configured in settings.py")
    
    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        try:
            # Create auth string and encode to base64
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode("ascii")
            auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
            
            headers = {
                "Authorization": f"Basic {auth_base64}"
            }
            
            response = requests.get(self.ACCESS_TOKEN_URL, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return response_data.get('access_token')
            else:
                logger.error(f"Error getting access token: {response_data}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate the password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password_bytes = password_str.encode('ascii')
        password_base64 = base64.b64encode(password_bytes).decode('ascii')
        
        return password_base64, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push to customer's phone"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'message': 'Could not get access token'
                }
            
            # Format phone number (remove leading 0 or +254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # Amount must be an integer
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            response = requests.post(self.STK_PUSH_URL, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'STK push initiated successfully',
                    'data': response_data
                }
            else:
                logger.error(f"STK push failed: {response_data}")
                return {
                    'success': False,
                    'message': f"STK push failed: {response_data.get('errorMessage', 'Unknown error')}",
                    'data': response_data
                }
                
        except Exception as e:
            logger.error(f"Exception initiating STK push: {str(e)}")
            return {
                'success': False,
                'message': f"Exception: {str(e)}"
            }
    
    def query_stk_status(self, checkout_request_id):
        """Query the status of an STK Push transaction"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'message': 'Could not get access token'
                }
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(self.QUERY_STK_STATUS_URL, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Query successful',
                    'data': response_data
                }
            else:
                logger.error(f"STK status query failed: {response_data}")
                return {
                    'success': False,
                    'message': f"Query failed: {response_data.get('errorMessage', 'Unknown error')}",
                    'data': response_data
                }
                
        except Exception as e:
            logger.error(f"Exception querying STK status: {str(e)}")
            return {
                'success': False,
                'message': f"Exception: {str(e)}"
            }

# Helper functions for processing M-Pesa callbacks
def process_stk_callback(callback_data):
    """Process the STK Push callback from M-Pesa"""
    try:
        # Extract the callback metadata
        callback_body = callback_data.get('Body', {})
        stkCallback = callback_body.get('stkCallback', {})
        result_code = stkCallback.get('ResultCode')
        result_desc = stkCallback.get('ResultDesc')
        checkout_request_id = stkCallback.get('CheckoutRequestID')
        merchant_request_id = stkCallback.get('MerchantRequestID')
        
        # If successful, extract the payment details
        if result_code == 0:  # 0 means success
            callback_metadata = stkCallback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            # Extract payment details from metadata items
            payment_details = {}
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                payment_details[name] = value
            
            return {
                'success': True,
                'result_code': result_code,
                'result_desc': result_desc,
                'checkout_request_id': checkout_request_id,
                'merchant_request_id': merchant_request_id,
                'mpesa_receipt_number': payment_details.get('MpesaReceiptNumber'),
                'transaction_date': payment_details.get('TransactionDate'),
                'phone_number': payment_details.get('PhoneNumber'),
                'amount': payment_details.get('Amount')
            }
        else:
            # Payment was not successful
            return {
                'success': False,
                'result_code': result_code,
                'result_desc': result_desc,
                'checkout_request_id': checkout_request_id,
                'merchant_request_id': merchant_request_id
            }
    
    except Exception as e:
        logger.error(f"Error processing STK callback: {str(e)}")
        return {
            'success': False,
            'message': f"Error processing callback: {str(e)}"
        }