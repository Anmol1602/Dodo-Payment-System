/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Customer, Invoice, PaymentAttempt, SystemLog, WebhookDelivery } from './types';
import {
  INITIAL_CUSTOMERS,
  INITIAL_INVOICES,
  INITIAL_LOGS,
  INITIAL_WEBHOOKS,
} from './data/mockData';
import { Header } from './components/Header';
import { NavTab, Sidebar } from './components/Sidebar';
import { MetricsCards } from './components/MetricsCards';
import { InvoiceTable } from './components/InvoiceTable';
import { CustomersView } from './components/CustomersView';
import { WebhooksView } from './components/WebhooksView';
import { LogsView } from './components/LogsView';
import { InvoiceDetailModal } from './components/InvoiceDetailModal';
import { CreateInvoiceModal } from './components/CreateInvoiceModal';

export default function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('invoices');
  const [invoices, setInvoices] = useState<Invoice[]>(INITIAL_INVOICES);
  const [customers, setCustomers] = useState<Customer[]>(INITIAL_CUSTOMERS);
  const [webhooks, setWebhooks] = useState<WebhookDelivery[]>(INITIAL_WEBHOOKS);
  const [logs, setLogs] = useState<SystemLog[]>(INITIAL_LOGS);

  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Computed metrics
  const totalVolumeCents = invoices
    .filter((inv) => inv.state === 'paid')
    .reduce((sum, inv) => sum + inv.totalAmountCents, 0);

  const totalAttempts = invoices.reduce((sum, inv) => sum + inv.attempts.length, 0);
  const successRatePercentage =
    totalAttempts > 0
      ? (
          (invoices.reduce(
            (sum, inv) =>
              sum + inv.attempts.filter((a) => a.status === 'succeeded').length,
            0
          ) /
            totalAttempts) *
          100
        ).toFixed(1)
      : '100.0';

  const formatCentsToCurrency = (cents: number): string => {
    return (cents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  // Simulate Payment Attempt
  const handleSimulatePayment = (
    invoiceId: string,
    token: 'tok_success' | 'tok_timeout' | 'tok_card_declined' | 'tok_insufficient_funds',
    idempotencyKey: string
  ) => {
    const targetInvoice = invoices.find((inv) => inv.id === invoiceId);
    if (!targetInvoice) return;

    if (targetInvoice.state === 'paid' || targetInvoice.state === 'void') {
      return;
    }

    const newAttemptId = `att_${Math.random().toString(36).substring(2, 9)}`;
    const now = new Date().toISOString();

    let newAttempt: PaymentAttempt;
    let nextState = targetInvoice.state;
    let nextLastPspResult: 'Succeeded' | 'Declined' | 'Pending' | 'Timeout' = 'Succeeded';

    if (token === 'tok_success') {
      newAttempt = {
        id: newAttemptId,
        invoiceId,
        tokenUsed: token,
        amountCents: targetInvoice.totalAmountCents,
        status: 'succeeded',
        pspResult: 'Succeeded',
        idempotencyKey,
        createdAt: now,
      };
      nextState = 'paid';
      nextLastPspResult = 'Succeeded';

      // Log success
      setLogs((prev) => [
        {
          id: `log_${Date.now()}`,
          timestamp: now,
          level: 'INFO',
          component: 'STATE_MACHINE',
          message: `Invoice ${targetInvoice.displayNumber} transitioned ${targetInvoice.state.toUpperCase()} -> PAID.`,
        },
        ...prev,
      ]);

      // Webhook dispatch
      setWebhooks((prev) => [
        {
          id: `wh_${Date.now()}`,
          eventType: 'invoice.paid',
          invoiceId,
          targetUrl: `https://${targetInvoice.customerEmail.split('@')[1] || 'client.com'}/webhooks/dodo`,
          statusCode: 200,
          status: 'delivered',
          attempts: 1,
          signature: `t=${Math.floor(Date.now() / 1000)},v1=${Math.random().toString(16).substring(2, 34)}`,
          timestamp: now,
          payload: {
            event: 'invoice.paid',
            data: {
              id: invoiceId,
              display_number: targetInvoice.displayNumber,
              amount_cents: targetInvoice.totalAmountCents,
              currency: 'USD',
              status: 'paid',
              customer: targetInvoice.customerEmail,
            },
          },
        },
        ...prev,
      ]);
    } else if (token === 'tok_timeout') {
      newAttempt = {
        id: newAttemptId,
        invoiceId,
        tokenUsed: token,
        amountCents: targetInvoice.totalAmountCents,
        status: 'pending',
        pspResult: 'Pending',
        failureCode: 'gateway_timeout',
        failureMessage: 'Payment processor timed out after 5.0s.',
        idempotencyKey,
        createdAt: now,
      };
      nextState = 'open';
      nextLastPspResult = 'Pending';

      setLogs((prev) => [
        {
          id: `log_${Date.now()}`,
          timestamp: now,
          level: 'WARN',
          component: 'PSP_WORKER',
          message: `Upstream PSP timeout (5.0s). Attempt recorded as PENDING. Invoice ${targetInvoice.displayNumber} kept OPEN.`,
        },
        ...prev,
      ]);
    } else {
      const isDeclined = token === 'tok_card_declined';
      newAttempt = {
        id: newAttemptId,
        invoiceId,
        tokenUsed: token,
        amountCents: targetInvoice.totalAmountCents,
        status: 'failed',
        pspResult: 'Declined',
        failureCode: isDeclined ? 'card_declined' : 'insufficient_funds',
        failureMessage: isDeclined
          ? 'The card token presented was declined by the issuer.'
          : 'Insufficient funds on credit token balance.',
        idempotencyKey,
        createdAt: now,
      };
      nextState = 'open';
      nextLastPspResult = 'Declined';

      setLogs((prev) => [
        {
          id: `log_${Date.now()}`,
          timestamp: now,
          level: 'WARN',
          component: 'STATE_MACHINE',
          message: `Invoice ${targetInvoice.displayNumber} payment attempt failed (${newAttempt.failureCode}). Invoice remains OPEN.`,
        },
        ...prev,
      ]);

      setWebhooks((prev) => [
        {
          id: `wh_${Date.now()}`,
          eventType: 'payment.failed',
          invoiceId,
          targetUrl: `https://${targetInvoice.customerEmail.split('@')[1] || 'client.com'}/webhooks/dodo`,
          statusCode: 503,
          status: 'retrying',
          attempts: 1,
          signature: `t=${Math.floor(Date.now() / 1000)},v1=${Math.random().toString(16).substring(2, 34)}`,
          timestamp: now,
          payload: {
            event: 'payment.failed',
            data: {
              id: invoiceId,
              failure_code: newAttempt.failureCode,
              message: newAttempt.failureMessage,
            },
          },
        },
        ...prev,
      ]);
    }

    const updatedInvoice: Invoice = {
      ...targetInvoice,
      state: nextState,
      updatedAt: now,
      lastToken: token,
      lastPspResult: nextLastPspResult,
      attempts: [...targetInvoice.attempts, newAttempt],
    };

    setInvoices((prev) =>
      prev.map((inv) => (inv.id === invoiceId ? updatedInvoice : inv))
    );

    setSelectedInvoice(updatedInvoice);
  };

  // Void Invoice
  const handleVoidInvoice = (invoiceId: string) => {
    const targetInvoice = invoices.find((inv) => inv.id === invoiceId);
    if (!targetInvoice || targetInvoice.state === 'paid') return;

    const now = new Date().toISOString();
    const updatedInvoice: Invoice = {
      ...targetInvoice,
      state: 'void',
      updatedAt: now,
    };

    setInvoices((prev) =>
      prev.map((inv) => (inv.id === invoiceId ? updatedInvoice : inv))
    );

    setSelectedInvoice(updatedInvoice);

    setLogs((prev) => [
      {
        id: `log_${Date.now()}`,
        timestamp: now,
        level: 'WARN',
        component: 'STATE_MACHINE',
        message: `Invoice ${targetInvoice.displayNumber} transitioned to VOID state.`,
      },
      ...prev,
    ]);
  };

  // Create Invoice
  const handleCreateInvoice = (newInvoice: Invoice) => {
    setInvoices((prev) => [newInvoice, ...prev]);
    setLogs((prev) => [
      {
        id: `log_${Date.now()}`,
        timestamp: new Date().toISOString(),
        level: 'INFO',
        component: 'FASTAPI_CORE',
        message: `POST /api/v1/invoices HTTP/1.1 201 Created [display_id=${newInvoice.displayNumber}]`,
      },
      ...prev,
    ]);
  };

  return (
    <div className="min-h-screen w-full bg-[#0f172a] text-slate-200 font-sans overflow-x-hidden relative flex flex-col">
      {/* Ambient Glowing Orbs */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/20 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px]"></div>
        <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-purple-600/10 rounded-full blur-[100px]"></div>
      </div>

      {/* Header */}
      <Header onNewInvoice={() => setIsCreateModalOpen(true)} />

      {/* Main Workspace */}
      <main className="relative z-10 flex-1 grid grid-cols-12 gap-6 p-4 sm:p-6 max-w-7xl w-full mx-auto">
        {/* Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
        />

        {/* Content Section */}
        <section className="col-span-12 lg:col-span-9 flex flex-col gap-6 overflow-hidden">
          {/* Metrics Overview Cards */}
          <MetricsCards
            totalVolume={formatCentsToCurrency(totalVolumeCents || 4210550)}
            successRate={`${successRatePercentage}%`}
            webhookStatus="Active"
          />

          {/* Tab Views */}
          {currentTab === 'invoices' && (
            <InvoiceTable
              invoices={invoices}
              onSelectInvoice={(inv) => setSelectedInvoice(inv)}
              onOpenCreateModal={() => setIsCreateModalOpen(true)}
            />
          )}

          {currentTab === 'customers' && (
            <CustomersView customers={customers} />
          )}

          {currentTab === 'webhooks' && (
            <WebhooksView webhooks={webhooks} />
          )}

          {currentTab === 'logs' && (
            <LogsView logs={logs} onClearLogs={() => setLogs([])} />
          )}
        </section>
      </main>

      {/* Modals */}
      <InvoiceDetailModal
        invoice={selectedInvoice}
        onClose={() => setSelectedInvoice(null)}
        onSimulatePayment={handleSimulatePayment}
        onVoidInvoice={handleVoidInvoice}
      />

      <CreateInvoiceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        customers={customers}
        onCreateInvoice={handleCreateInvoice}
      />
    </div>
  );
}
