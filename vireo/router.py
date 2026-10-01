"""
Vireo Audio Support Ticket Router
Implements routing policies defined in Vireo Customer Support Operating Policy v3.2 §6.
"""

from typing import Dict, Any, Optional


SLA_TARGETS_MINUTES = {
    'chat': 15,
    'voice': 120,      # 2 hours
    'social': 240,     # 4 hours
    'email': 480       # 8 hours
}

TRANSFER_COST_INR = 305
BREACH_CREDIT_INR = 350


class TicketRouter:
    """
    Routes tickets to the optimal team based on category, channel, and customer context.
    Eliminates internal hand-offs and SLA breach penalties.
    """

    def __init__(self):
        pass

    def route(self, category: str, channel: str = 'chat', customer_care_plus: str = 'N', priority: str = 'Normal') -> Dict[str, Any]:
        """
        Determines the assigned team, tier, SLA target, and policy justification.
        """
        channel_clean = (channel or 'chat').lower()
        sla_target = SLA_TARGETS_MINUTES.get(channel_clean, 15)

        # 1. Specialized Departments (Policy §6)
        if category == 'Delivery & Shipping':
            return {
                'assigned_team': 'Logistics',
                'tier': 1,
                'channel': channel_clean,
                'sla_target_minutes': sla_target,
                'sop_clause': 'Policy §6: Logistics owns delivery, tracking, and reshipment.',
                'transfer_avoided': True
            }

        if category == 'Billing & Payments':
            return {
                'assigned_team': 'Billing',
                'tier': 1,
                'channel': channel_clean,
                'sla_target_minutes': sla_target,
                'sop_clause': 'Policy §6: Billing owns payments, invoices, refunds, and gateway queries.',
                'transfer_avoided': True
            }

        if category == 'Returns & Refunds':
            return {
                'assigned_team': 'Returns Desk',
                'tier': 1,
                'channel': channel_clean,
                'sla_target_minutes': sla_target,
                'sop_clause': 'Policy §6: Returns Desk owns return pickups and refund processing.',
                'transfer_avoided': True
            }

        if category == 'Warranty & Repair':
            return {
                'assigned_team': 'Escalations & Warranty',
                'tier': 2,
                'channel': channel_clean,
                'sla_target_minutes': sla_target,
                'sop_clause': 'Policy §6: Escalations & Warranty (Tier 2) owns RMA, warranty claims, and certified hardware repairs.',
                'transfer_avoided': True
            }

        # 2. General / Technical Frontline (Routed by Channel)
        # Policy §6: "Chat, Email and Voice Frontline (Tier 1) own first contact for product, account and general queries."
        if channel_clean in ('chat', 'social'):
            assigned_team = 'Chat Frontline'
        elif channel_clean == 'email':
            assigned_team = 'Email Frontline'
        elif channel_clean == 'voice':
            assigned_team = 'Voice Frontline'
        else:
            assigned_team = 'Chat Frontline'

        # Care Plus fast-track notice
        is_fast_track = (customer_care_plus == 'Y')

        return {
            'assigned_team': assigned_team,
            'tier': 1,
            'channel': channel_clean,
            'sla_target_minutes': sla_target,
            'care_plus_priority': is_fast_track,
            'sop_clause': f'Policy §6: Frontline ({assigned_team}) owns general product, audio, connectivity, and account support.',
            'transfer_avoided': False
        }
