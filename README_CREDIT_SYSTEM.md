# Marketing Credits Purchase & Management System

## System Architecture

The Marketing Credits Purchase & Management System is a comprehensive solution for managing a credit-based marketing campaign platform. This system allows businesses to purchase credits via M-Pesa or bank transfers, which can then be used to run marketing campaigns through the Influenza Platform.

### Core Components

1. **Credit Wallet System**
   - Business Credit Wallets: Individual wallets for each business user
   - Master Wallet: Admin-controlled central wallet for credit management
   - Transaction Ledger: Records all credit movements with double-entry accounting

2. **Payment Integration**
   - M-Pesa Integration via Safaricom Daraja API
   - Bank Transfer processing with manual verification

3. **Campaign Credit Management**
   - Credit check before campaign submission
   - Automatic credit deduction upon campaign approval
   - Campaign credit ledger for tracking credits used per campaign

4. **Admin Management**
   - Master dashboard for credit oversight
   - Business credit management tools
   - Reconciliation and reporting features
   - Invoice and receipt management

## Credit Flow Diagram

```
┌─────────────────┐     Purchase Credits     ┌─────────────────┐
│                 │ ─────────────────────────>│                 │
│  Business User  │                          │  Master Wallet  │
│  Credit Wallet  │ <─────────────────────── │  (Admin)        │
│                 │     Credits Added         │                 │
└────────┬────────┘                          └────────┬────────┘
         │                                            │
         │ Credits Used                               │ System
         │ for Campaign                               │ Reconciliation
         ▼                                            ▼
┌─────────────────┐                          ┌─────────────────┐
│                 │                          │                 │
│    Campaign     │                          │  Reconciliation │
│  Credit Ledger  │                          │     Reports     │
│                 │                          │                 │
└─────────────────┘                          └─────────────────┘
```

## Models Overview

### MasterWallet
- Singleton model for admin credit management
- Tracks total credits in the system
- Manages credit allocation and reconciliation

### CreditWallet
- Individual wallet for each business user
- Methods for adding and deducting credits
- Tracks current balance and transaction history

### Transaction
- Records all credit movements with double-entry accounting
- Types: purchase, campaign_deduction, refund, adjustment
- Maintains audit trail for all credit operations

### CampaignCreditLedger
- Links campaigns to credit transactions
- Tracks credits allocated to each campaign
- Enables campaign-specific reporting

### MpesaPayment
- Records M-Pesa transactions for credit purchases
- Stores transaction details from Safaricom API
- Links to Transaction model for credit allocation

### BankTransfer
- Records bank transfer details for credit purchases
- Includes verification status and admin approval
- Links to Transaction model upon verification

### Reconciliation
- Daily audit of credit balances across the system
- Identifies and reports discrepancies
- Maintains historical record of system reconciliation

## Implementation Details

### Payment Processing

1. **M-Pesa Integration**
   - Uses Safaricom Daraja API for STK Push
   - Real-time payment confirmation via callbacks
   - Automatic credit allocation upon successful payment

2. **Bank Transfer Processing**
   - Manual verification by admin users
   - Reference number tracking for payment matching
   - Credit allocation upon admin approval

### Credit Management

1. **Business User Features**
   - Credit purchase via multiple payment methods
   - Transaction history with downloadable receipts
   - Credit usage tracking per campaign
   - Dashboard with credit statistics
   - View and download invoices
   - Invoice and receipt management

2. **Admin Features**
   - Master credit dashboard
   - Business credit management
   - Manual credit allocation with invoice generation
   - Invoice and receipt management
   - Daily reconciliation
   - System reports and analytics

### Campaign Integration

1. **Credit Check**
   - Pre-submission credit verification
   - Dynamic credit cost calculation based on campaign budget

2. **Credit Deduction**
   - Automatic deduction upon campaign approval
   - Credit refund for rejected campaigns
   - Campaign credit ledger for tracking

## Detailed Admin Features

### Master Dashboard
- View total credits in the system
- Monitor credit distribution across businesses
- Track credit usage trends

### Credit Management
- View all business credit wallets and balances
- Manually allocate credits to businesses
- Adjust credit balances when necessary

### Manual Credit Allocation
- Allocate credits to businesses manually
- Record reason for allocation
- Track manual allocations in transaction history
- Generate invoices for manual allocations

### Reconciliation
- Daily reconciliation of credit balances
- Identify and resolve discrepancies
- Generate reconciliation reports

### Invoice and Receipt Management
- Create new invoices for businesses
- View all invoices in the system
- Mark invoices as paid
- Generate receipts for paid invoices
- Download invoice and receipt PDFs

### Reports
- Credit usage reports
- Transaction reports
- Revenue reports from credit purchases
- Invoice status reports