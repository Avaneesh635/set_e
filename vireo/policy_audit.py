"""
Vireo Audio Support Desk Policy & Compliance Audit Engine
Audits operations against Customer Support Operating Policy v3.2.
Detects illegal double-compensations (Policy §5), goodwill credit cap breaches, and data reconciliations.
"""

import csv
from collections import defaultdict
from typing import Dict, List, Any


REPLACEMENT_SHIPPING_INR = 340
GOODWILL_CAP_INR = 500


class PolicyAuditor:
    """
    Audits compliance with Vireo Customer Support Operating Policy v3.2.
    """

    def __init__(self,
                 tickets_path: str = 'tickets.csv',
                 orders_path: str = 'orders.csv',
                 products_path: str = 'products.csv',
                 customers_path: str = 'customers.csv'):
        self.tickets_path = tickets_path
        self.orders_path = orders_path
        self.products_path = products_path
        self.customers_path = customers_path

        self.tickets = []
        self.orders = {}
        self.products = {}
        self.customers = {}
        self._load_data()

    def _load_data(self):
        with open(self.products_path, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                self.products[r['sku']] = r

        with open(self.customers_path, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                self.customers[r['customer_id']] = r

        with open(self.orders_path, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                self.orders[r['order_id']] = r

        with open(self.tickets_path, 'r', encoding='utf-8') as f:
            self.tickets = list(csv.DictReader(f))

    def audit_double_compensation(self) -> Dict[str, Any]:
        """
        Policy §5: 'In no case is a customer to receive both a refund and a replacement
        for the same order; where this happens in error it must be escalated to the Team Lead
        and Finance the same day.'

        Detects all orders that received both a refund and a replacement.
        """
        order_ticket_actions = defaultdict(lambda: {'refunds': [], 'replacements': []})

        for t in self.tickets:
            oid = t.get('order_id', '').strip()
            # If order_id blank, fallback join: customer_id + product_sku (per README.txt)
            if not oid:
                cid = t.get('customer_id', '')
                sku = t.get('product_sku', '')
                if cid and sku:
                    for test_oid, o in self.orders.items():
                        if o['customer_id'] == cid and o['sku'] == sku:
                            oid = test_oid
                            break

            if not oid:
                continue

            if t.get('refund_amount_inr'):
                order_ticket_actions[oid]['refunds'].append(t)
            if t.get('replacement_issued') == 'Y':
                order_ticket_actions[oid]['replacements'].append(t)

        double_cases = []
        total_refund_leakage = 0.0
        total_repl_cost_leakage = 0.0

        for oid, actions in order_ticket_actions.items():
            if actions['refunds'] and actions['replacements']:
                order_info = self.orders.get(oid, {})
                sku = order_info.get('sku') or (actions['replacements'][0].get('product_sku') if actions['replacements'] else '')
                prod_info = self.products.get(sku, {})

                unit_cost = float(prod_info.get('unit_cost_inr', 0)) if prod_info else 0.0
                repl_cost = unit_cost + REPLACEMENT_SHIPPING_INR if unit_cost > 0 else 0.0

                rf_sum = sum(float(t['refund_amount_inr']) for t in actions['refunds'] if t.get('refund_amount_inr'))

                total_refund_leakage += rf_sum
                total_repl_cost_leakage += repl_cost

                double_cases.append({
                    'order_id': oid,
                    'customer_id': order_info.get('customer_id', actions['refunds'][0].get('customer_id', '')),
                    'customer_name': self.customers.get(order_info.get('customer_id', ''), {}).get('name', 'Unknown'),
                    'product_sku': sku,
                    'product_name': prod_info.get('product_name', 'Unknown'),
                    'refund_amount_inr': rf_sum,
                    'refund_tickets': [t['ticket_id'] for t in actions['refunds']],
                    'replacement_tickets': [t['ticket_id'] for t in actions['replacements']],
                    'replacement_unit_cost_inr': unit_cost,
                    'replacement_total_cost_inr': repl_cost,
                    'total_financial_loss_inr': rf_sum + repl_cost
                })

        double_cases.sort(key=lambda x: -x['total_financial_loss_inr'])

        return {
            'total_double_compensated_orders': len(double_cases),
            'total_refund_leakage_inr': round(total_refund_leakage, 2),
            'total_replacement_cost_leakage_inr': round(total_repl_cost_leakage, 2),
            'total_financial_loss_inr': round(total_refund_leakage + total_repl_cost_leakage, 2),
            'cases': double_cases
        }

    def audit_goodwill_cap(self) -> Dict[str, Any]:
        """
        Policy §5: 'Goodwill credits are capped at Rs 500 per ticket and require Team Lead approval.'
        """
        breaches = []
        for t in self.tickets:
            if t.get('refund_reason_code') == 'GW-OTHER':
                rf_str = t.get('refund_amount_inr', '')
                if rf_str:
                    val = float(rf_str)
                    if val > GOODWILL_CAP_INR:
                        breaches.append({
                            'ticket_id': t['ticket_id'],
                            'customer_id': t['customer_id'],
                            'refund_amount_inr': val,
                            'excess_amount_inr': val - GOODWILL_CAP_INR,
                            'agent_id': t['agent_id'],
                            'notes': t['agent_notes']
                        })

        return {
            'goodwill_breaches_count': len(breaches),
            'total_excess_inr': sum(b['excess_amount_inr'] for b in breaches),
            'breaches': breaches
        }

    def run_all_audits(self) -> Dict[str, Any]:
        return {
            'double_compensation': self.audit_double_compensation(),
            'goodwill_cap': self.audit_goodwill_cap()
        }
