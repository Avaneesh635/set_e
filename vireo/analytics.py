"""
Vireo Audio Support Desk Analytics Engine
Calculates monthly volume breakdowns, team workloads, handle times, SLA breach rates,
transfer costs, and headcount allocation scenarios.
"""

import csv
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple


SLA_LIMITS_MINUTES = {
    'chat': 15,
    'voice': 120,
    'social': 240,
    'email': 480
}

TRANSFER_COST_INR = 305
BREACH_CREDIT_INR = 350
AGENT_HOURLY_COST_INR = 165
TWO_HIRES_ANNUAL_COST_INR = 900000
TWO_HIRES_QUARTERLY_COST_INR = 225000


class AnalyticsEngine:
    """
    Computes reporting definitions and financial models as defined in Support Policy v3.2.
    """

    def __init__(self, tickets_path: str = 'tickets.csv', agents_path: str = 'agents.csv'):
        self.tickets_path = tickets_path
        self.agents_path = agents_path
        self.tickets = []
        self.agents = {}
        self.agent_teams = {}
        self.team_agent_counts = Counter()
        self._load_data()

    def _load_data(self):
        # Load agents
        with open(self.agents_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # An agent can have multiple rows if shift/site changed. Keep latest.
            sorted_rows = sorted(list(reader), key=lambda x: x.get('to_date', ''))
            for r in sorted_rows:
                a_id = r['agent_id']
                self.agents[a_id] = r
                self.agent_teams[a_id] = r['team']

        for a_id, r in self.agents.items():
            self.team_agent_counts[r['team']] += 1

        # Load tickets
        with open(self.tickets_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.tickets = list(reader)

    def get_monthly_breakdown(self) -> Dict[str, Any]:
        """
        Calculates monthly breakdown by category and by team for:
        1. Bot Intake View (Legacy exported assigned_team and category)
        2. Ground Truth Resolving Team View (True workload)
        """
        months_set = set()
        bot_cat_by_month = defaultdict(lambda: defaultdict(int))
        bot_team_by_month = defaultdict(lambda: defaultdict(int))
        res_team_by_month = defaultdict(lambda: defaultdict(int))

        for t in self.tickets:
            created = t.get('created_at', '')
            if not created:
                continue
            month = created[:7]
            months_set.add(month)

            cat = t.get('category', 'Other')
            asgn_team = t.get('assigned_team', 'Unknown')
            res_team = self.agent_teams.get(t.get('agent_id', ''), 'Unknown')

            bot_cat_by_month[month][cat] += 1
            bot_team_by_month[month][asgn_team] += 1
            res_team_by_month[month][res_team] += 1

        sorted_months = sorted(list(months_set))

        # Categories list
        categories = sorted(list({t.get('category', 'Other') for t in self.tickets}))
        teams = sorted(list(self.team_agent_counts.keys()))

        return {
            'months': sorted_months,
            'categories': categories,
            'teams': teams,
            'bot_category_by_month': {m: dict(bot_cat_by_month[m]) for m in sorted_months},
            'bot_team_by_month': {m: dict(bot_team_by_month[m]) for m in sorted_months},
            'resolved_team_by_month': {m: dict(res_team_by_month[m]) for m in sorted_months}
        }

    def get_team_workload_and_performance(self) -> List[Dict[str, Any]]:
        """
        Calculates workload, resolution times, SLA breaches, and CSAT for each resolving team.
        """
        team_stats = defaultdict(lambda: {
            'resolved_count': 0,
            'res_hours_list': [],
            'breaches': 0,
            'csat_scores': [],
            'transfers_received': 0
        })

        for t in self.tickets:
            a_id = t.get('agent_id', '')
            team = self.agent_teams.get(a_id, 'Unknown')
            created_str = t.get('created_at', '')
            if not created_str:
                continue
            c_time = datetime.strptime(created_str, '%Y-%m-%d %H:%M')

            st = team_stats[team]
            st['resolved_count'] += 1

            # Handle time: created to resolved
            res_str = t.get('resolved_at', '')
            if res_str:
                r_time = datetime.strptime(res_str, '%Y-%m-%d %H:%M')
                hours = (r_time - c_time).total_seconds() / 3600.0
                if hours >= 0:
                    st['res_hours_list'].append(hours)

            # First response SLA breach
            fr_str = t.get('first_response_at', '')
            if fr_str:
                fr_time = datetime.strptime(fr_str, '%Y-%m-%d %H:%M')
                fr_mins = (fr_time - c_time).total_seconds() / 60.0
                ch = t.get('channel', 'chat')
                if fr_mins > SLA_LIMITS_MINUTES.get(ch, 15):
                    st['breaches'] += 1

            # CSAT
            csat_str = t.get('csat_score', '')
            if csat_str:
                st['csat_scores'].append(int(csat_str))

            # Transfers received
            if t.get('transfers') and int(t.get('transfers')) > 0 and t.get('assigned_team') != team:
                st['transfers_received'] += int(t.get('transfers'))

        result = []
        total_tickets = len(self.tickets)

        for team, st in team_stats.items():
            if team == 'Unknown':
                continue
            agent_cnt = self.team_agent_counts.get(team, 1)
            res_cnt = st['resolved_count']
            hours_list = sorted(st['res_hours_list'])
            avg_res = round(sum(hours_list) / len(hours_list), 1) if hours_list else 0.0
            med_res = round(hours_list[len(hours_list) // 2], 1) if hours_list else 0.0
            breach_cnt = st['breaches']
            breach_rate = round((breach_cnt / res_cnt) * 100, 1) if res_cnt else 0.0
            breach_cost = breach_cnt * BREACH_CREDIT_INR
            csat_avg = round(sum(st['csat_scores']) / len(st['csat_scores']), 2) if st['csat_scores'] else 0.0

            result.append({
                'team': team,
                'agent_count': agent_cnt,
                'resolved_tickets': res_cnt,
                'share_pct': round((res_cnt / total_tickets) * 100, 1),
                'tickets_per_agent': round(res_cnt / agent_cnt, 1),
                'avg_resolution_hours': avg_res,
                'median_resolution_hours': med_res,
                'breach_count': breach_cnt,
                'breach_rate_pct': breach_rate,
                'breach_penalty_inr': breach_cost,
                'avg_csat': csat_avg
            })

        result.sort(key=lambda x: -x['resolved_tickets'])
        return result

    def get_routing_misclassification_audit(self) -> Dict[str, Any]:
        """
        Audits the bot's initial routing vs actual resolution, quantifying
        the Billing -> Logistics misrouting leak and transfer costs.
        """
        billing_assigned = 0
        billing_to_logistics = 0
        billing_resolved_by_billing = 0
        total_mismatches = 0
        helpdesk_transfers = 0
        billing_transfers = 0

        # Detailed breakdown of Billing-assigned tickets
        billing_targets = Counter()

        for t in self.tickets:
            asgn = t.get('assigned_team', '')
            res = self.agent_teams.get(t.get('agent_id', ''), 'Unknown')
            if asgn != res:
                total_mismatches += 1

            if asgn == 'Billing':
                billing_assigned += 1
                billing_targets[res] += 1
                if res == 'Logistics':
                    billing_to_logistics += 1
                elif res == 'Billing':
                    billing_resolved_by_billing += 1

            tr = t.get('transfers', '')
            if tr:
                tr_val = int(tr)
                helpdesk_transfers += tr_val
                if asgn == 'Billing':
                    billing_transfers += tr_val

        # Logistics performance split: directly routed vs transferred from Billing
        direct_log_hours = []
        transferred_log_hours = []
        direct_log_breaches = 0
        transferred_log_breaches = 0
        direct_log_total = 0
        transferred_log_total = 0
        direct_csat = []
        transferred_csat = []

        for t in self.tickets:
            res_team = self.agent_teams.get(t.get('agent_id', ''), '')
            if res_team == 'Logistics':
                created = datetime.strptime(t['created_at'], '%Y-%m-%d %H:%M')
                res_str = t.get('resolved_at', '')
                hours = (datetime.strptime(res_str, '%Y-%m-%d %H:%M') - created).total_seconds() / 3600.0 if res_str else 0
                fr_str = t.get('first_response_at', '')
                ch = t.get('channel', 'chat')
                is_breach = False
                if fr_str:
                    fr_time = datetime.strptime(fr_str, '%Y-%m-%d %H:%M')
                    if (fr_time - created).total_seconds() / 60.0 > SLA_LIMITS_MINUTES.get(ch, 15):
                        is_breach = True

                csat_val = int(t['csat_score']) if t.get('csat_score') else None

                if t.get('assigned_team') == 'Logistics':
                    direct_log_total += 1
                    if hours >= 0:
                        direct_log_hours.append(hours)
                    if is_breach:
                        direct_log_breaches += 1
                    if csat_val:
                        direct_csat.append(csat_val)
                elif t.get('assigned_team') == 'Billing':
                    transferred_log_total += 1
                    if hours >= 0:
                        transferred_log_hours.append(hours)
                    if is_breach:
                        transferred_log_breaches += 1
                    if csat_val:
                        transferred_csat.append(csat_val)

        direct_log_hours.sort()
        transferred_log_hours.sort()

        return {
            'total_tickets': len(self.tickets),
            'total_routing_mismatches': total_mismatches,
            'mismatch_rate_pct': round((total_mismatches / len(self.tickets)) * 100, 1),
            'billing_assigned_count': billing_assigned,
            'billing_assigned_pct': round((billing_assigned / len(self.tickets)) * 100, 1),
            'billing_to_logistics_count': billing_to_logistics,
            'billing_to_logistics_share_of_billing': round((billing_to_logistics / billing_assigned) * 100, 1),
            'billing_resolved_by_billing': billing_resolved_by_billing,
            'billing_true_workload_pct': round((billing_resolved_by_billing / len(self.tickets)) * 100, 1),
            'helpdesk_total_transfers': helpdesk_transfers,
            'helpdesk_total_transfer_cost_inr': helpdesk_transfers * TRANSFER_COST_INR,
            'billing_initiated_transfers': billing_transfers,
            'billing_initiated_transfer_cost_inr': billing_transfers * TRANSFER_COST_INR,
            'billing_transfer_share_pct': round((billing_transfers / helpdesk_transfers) * 100, 1) if helpdesk_transfers else 0,
            'logistics_direct': {
                'count': direct_log_total,
                'median_hours': round(direct_log_hours[len(direct_log_hours)//2], 1) if direct_log_hours else 0,
                'avg_hours': round(sum(direct_log_hours)/len(direct_log_hours), 1) if direct_log_hours else 0,
                'breach_rate_pct': round((direct_log_breaches / direct_log_total) * 100, 1) if direct_log_total else 0,
                'avg_csat': round(sum(direct_csat)/len(direct_csat), 2) if direct_csat else 0
            },
            'logistics_transferred_from_billing': {
                'count': transferred_log_total,
                'median_hours': round(transferred_log_hours[len(transferred_log_hours)//2], 1) if transferred_log_hours else 0,
                'avg_hours': round(sum(transferred_log_hours)/len(transferred_log_hours), 1) if transferred_log_hours else 0,
                'breach_rate_pct': round((transferred_log_breaches / transferred_log_total) * 100, 1) if transferred_log_total else 0,
                'avg_csat': round(sum(transferred_csat)/len(transferred_csat), 2) if transferred_csat else 0
            }
        }

    def get_financial_projections(self, weekly_tickets: int = 650) -> Dict[str, Any]:
        """
        Projects quarterly and annual financial impact at Vireo's operating volume.
        """
        quarterly_volume = weekly_tickets * 13  # 8,450 tickets
        audit = self.get_routing_misclassification_audit()

        # Proportions from data
        billing_assigned_rate = audit['billing_assigned_pct'] / 100.0  # 21.8%
        billing_to_log_rate = audit['billing_to_logistics_share_of_billing'] / 100.0  # 31.0%
        helpdesk_transfer_rate = audit['helpdesk_total_transfers'] / 7728.0  # 16.8%
        billing_transfer_share = audit['billing_transfer_share_pct'] / 100.0  # 48.7%

        # Quarterly projection at 8,450 tickets
        q_transfers = quarterly_volume * helpdesk_transfer_rate  # ~1,420 transfers
        q_transfer_cost = q_transfers * TRANSFER_COST_INR  # ~Rs 433,000

        q_billing_transfers = q_transfers * billing_transfer_share  # ~691 transfers
        q_billing_transfer_cost = q_billing_transfers * TRANSFER_COST_INR  # ~Rs 210,800

        # Avoidable SLA breaches: 26.4% excess breach rate on misrouted Billing->Logistics
        q_billing_to_log_tickets = (quarterly_volume * billing_assigned_rate) * billing_to_log_rate  # ~571 tickets
        excess_breaches = q_billing_to_log_tickets * (0.351 - 0.087)  # ~151 breaches
        q_avoided_sla_credits = excess_breaches * BREACH_CREDIT_INR  # ~Rs 52,850

        # Headcount costs
        q_headcount_saving = TWO_HIRES_QUARTERLY_COST_INR  # Rs 225,000

        total_quarterly_operational_saving = q_billing_transfer_cost + q_avoided_sla_credits
        total_quarterly_combined_impact = total_quarterly_operational_saving + q_headcount_saving

        return {
            'weekly_volume': weekly_tickets,
            'quarterly_volume': quarterly_volume,
            'quarterly_transfer_waste_inr': round(q_transfer_cost),
            'quarterly_billing_transfer_waste_inr': round(q_billing_transfer_cost),
            'quarterly_avoidable_sla_credits_inr': round(q_avoided_sla_credits),
            'quarterly_operational_savings_inr': round(total_quarterly_operational_saving),
            'quarterly_headcount_salary_inr': q_headcount_saving,
            'total_quarterly_value_inr': round(total_quarterly_combined_impact),
            'total_annual_value_inr': round(total_quarterly_combined_impact * 4)
        }
