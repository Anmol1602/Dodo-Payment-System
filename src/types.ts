export type InvoiceState = 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';

export interface LineItem {
  id: string;
  description: string;
  quantity: number;
  unitAmountCents: number;
  totalAmountCents: number;
}

export interface PaymentAttempt {
  id: string;
  invoiceId: string;
  tokenUsed: 'tok_success' | 'tok_timeout' | 'tok_card_declined' | 'tok_insufficient_funds';
  amountCents: number;
  status: 'succeeded' | 'failed' | 'pending';
  pspResult: 'Succeeded' | 'Declined' | 'Pending' | 'Timeout';
  failureCode?: string;
  failureMessage?: string;
  idempotencyKey: string;
  createdAt: string;
}

export interface Invoice {
  id: string;
  displayNumber: string;
  businessId: string;
  customerId: string;
  customerName: string;
  customerEmail: string;
  state: InvoiceState;
  currency: 'USD';
  totalAmountCents: number;
  dueDate: string;
  createdAt: string;
  updatedAt: string;
  lineItems: LineItem[];
  attempts: PaymentAttempt[];
  lastToken?: string;
  lastPspResult?: 'Succeeded' | 'Declined' | 'Pending' | 'Timeout';
}

export interface Customer {
  id: string;
  businessId: string;
  name: string;
  email: string;
  createdAt: string;
  totalSpentCents: number;
  invoiceCount: number;
}

export interface WebhookDelivery {
  id: string;
  eventType: 'invoice.paid' | 'payment.failed' | 'invoice.created' | 'invoice.voided';
  invoiceId: string;
  targetUrl: string;
  statusCode: number;
  status: 'delivered' | 'retrying' | 'failed';
  attempts: number;
  signature: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface SystemLog {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  component: 'FASTAPI_CORE' | 'STATE_MACHINE' | 'IDEMPOTENCY' | 'PSP_WORKER' | 'WEBHOOK_DISPATCHER';
  message: string;
  details?: Record<string, unknown>;
}
