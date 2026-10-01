"""
Vireo Audio Ticket Classifier
Hybrid Domain Intent & N-gram Naive Bayes Classifier
Runs purely on Python 3 standard library (zero external dependencies).
"""

import re
import math
from collections import defaultdict, Counter


CATEGORIES = [
    "Delivery & Shipping",
    "Billing & Payments",
    "Returns & Refunds",
    "Warranty & Repair",
    "Connectivity",
    "Charging & Battery",
    "Audio Quality",
    "App & Firmware",
    "Account & Login",
    "Product Enquiry",
    "Other"
]


def tokenize(text):
    """Tokenize customer message into unigrams and bigrams with typo tolerance."""
    if not text:
        return []
    text = text.lower()
    # Normalize common abbreviations and typos in Indian e-commerce support
    text = re.sub(r'\b(dlvry|delivry|delvry)\b', 'delivery', text)
    text = re.sub(r'\b(ord|odrer|odr)\b', 'order', text)
    text = re.sub(r'\b(pkp|pckup|pick-up)\b', 'pickup', text)
    text = re.sub(r'\b(rcvd|recieved|recvd)\b', 'received', text)
    text = re.sub(r'\b(rfnd|refnd)\b', 'refund', text)
    text = re.sub(r'\b(wty|waranty|warrenty)\b', 'warranty', text)
    text = re.sub(r'\b(crr|coureir)\b', 'courier', text)
    text = re.sub(r'\b(bt|blutooth)\b', 'bluetooth', text)
    
    words = re.findall(r'[a-z0-9]+', text)
    tokens = list(words)
    # Add adjacent bigrams for phrase capturing
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]}_{words[i+1]}")
    return tokens


def infer_ground_truth(ticket, agent_teams):
    """
    Infers the true category and resolving team for a historical ticket.
    Uses agent notes, refund codes, replacement flag, and resolving agent roster.
    """
    notes = (ticket.get('agent_notes') or '').lower()
    res_team = agent_teams.get(ticket.get('agent_id', ''), '')
    cat = ticket.get('category', '')
    ref_code = ticket.get('refund_reason_code', '')
    repl_flag = ticket.get('replacement_issued', '')
    channel = ticket.get('channel', 'chat')

    # 1. Delivery & Shipping (Logistics)
    if (res_team == 'Logistics' or
        ref_code == 'LOST-TRANSIT' or
        any(k in notes for k in [
            'shipment not', 'order not delivered', 'ord not delivered',
            'delivery delayed', 'dlvry delayed', 'courier confirmed',
            're-shipped from warehouse', 'rto confirmed', 'address update',
            'wrong item delivered', 'damaged in transit', 'courier partner',
            'parcel stuck', 'lost in transit', 'misrouted - dlvry',
            'payment ok. shipment issue', 'not a billing issue - delivery',
            'cx paid fine, parcel stuck'
        ])):
        return 'Delivery & Shipping', 'Logistics'

    # 2. Returns & Refunds (Returns Desk)
    if (res_team == 'Returns Desk' or
        ref_code in ('RETURN-QC-OK', 'DOA-REPL') or
        any(k in notes for k in [
            'reverse pickup', 'pickup done', 'pkp missed', 'pkp not done',
            'pickup pending', 'return pickup', 'qc passed', 'qc failed',
            'return received'
        ])):
        return 'Returns & Refunds', 'Returns Desk'

    # 3. Warranty & Repair (Escalations & Warranty - Tier 2)
    if (res_team == 'Escalations & Warranty' or
        ref_code == 'WTY-BUYBACK' or
        repl_flag == 'Y' or
        any(k in notes for k in [
            'warranty', 'rma', 'service centre', 'service center',
            'hardware defect', 'tier 2', 'escalated to wty', 'buyback',
            'replacement approved'
        ])):
        return 'Warranty & Repair', 'Escalations & Warranty'

    # 4. Billing & Payments (Billing)
    if (res_team == 'Billing' or
        ref_code in ('DUP-PAYMENT', 'PRICE-ADJ', 'CANCEL') or
        any(k in notes for k in [
            'double charge', 'charged twice', 'duplicate txn',
            'failed order after payment', 'amount deducted without ord',
            'payment gateway', 'gst invoice', 'tax bill', 'coupon code',
            'discount not applied', 'cancellation request',
            'cancelled before dispatch', 'refund not credited',
            'refund pending', 'invoice emailed'
        ])):
        return 'Billing & Payments', 'Billing'

    # 5. Technical Frontline Categories (routed to Frontline by channel)
    frontline_team = 'Chat Frontline' if channel in ('chat', 'social') else 'Email Frontline' if channel == 'email' else 'Voice Frontline'

    if any(k in notes for k in ['pairing', 'bluetooth', 'disconnect', 'unable to pair', 'device not discoverable', 'bt dropouts']):
        return 'Connectivity', frontline_team

    if any(k in notes for k in ['battery', 'charge', 'charging', 'drain', 'backup']):
        return 'Charging & Battery', frontline_team

    if any(k in notes for k in ['audio', 'sound', 'mic', 'microphone', 'low volume', 'distortion', 'crackling', 'bass']):
        return 'Audio Quality', frontline_team

    if any(k in notes for k in ['app', 'firmware', 'update', 'sync', 'crash']):
        return 'App & Firmware', frontline_team

    if any(k in notes for k in ['login', 'otp', 'password', 'account']):
        return 'Account & Login', frontline_team

    if any(k in notes for k in ['product enquiry', 'compatibility', 'specs', 'pre-purchase']):
        return 'Product Enquiry', frontline_team

    # Fallback to category if not Other
    if cat and cat != 'Other':
        return cat, res_team or ticket.get('assigned_team', frontline_team)

    return 'Other', res_team or ticket.get('assigned_team', frontline_team)


class TicketClassifier:
    """
    High-speed, production-grade text classifier for support tickets.
    Combines domain-specific intent rules with Laplace-smoothed Naive Bayes.
    """

    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.cat_doc_counts = Counter()
        self.cat_word_counts = defaultdict(Counter)
        self.cat_total_words = defaultdict(int)
        self.vocab = set()
        self.num_docs = 0
        self.is_trained = False

    def train(self, training_records):
        """
        Train classifier on records containing 'message' and 'gt_category'.
        training_records: list of dicts.
        """
        self.cat_doc_counts.clear()
        self.cat_word_counts.clear()
        self.cat_total_words.clear()
        self.vocab.clear()

        for d in training_records:
            cat = d['gt_category']
            toks = tokenize(d['message'])
            self.cat_doc_counts[cat] += 1
            for t in toks:
                self.cat_word_counts[cat][t] += 1
                self.cat_total_words[cat] += 1
                self.vocab.add(t)

        self.num_docs = len(training_records)
        self.is_trained = True

    def _apply_domain_intent_rules(self, text):
        """
        Applies high-confidence intent disambiguation rules.
        Crucially resolves the 'Paid but not delivered' conflict:
        When a customer mentions payment ('paid', 'money debited') but the active issue
        is delivery tracking, non-arrival, or courier delay, intent is Delivery & Shipping!
        """
        m = text.lower()

        # 1. Non-delivery / Courier delay takes absolute precedence over payment mentions
        # E.g. "paid 5 days ago, package not delivered yet" -> Delivery & Shipping
        has_delivery_intent = any(re.search(p, m) for p in [
            r'not delivered', r'never delivered', r'haven\'?t received', r'hasn\'?t arrived',
            r'not received', r'where is my', r'package not', r'order not arrived',
            r'item not with me', r'nothing at my door', r'out for delivery', r'tracking',
            r'courier', r'awb', r'delivery delayed', r'dlvry', r'rto', r'wrong item',
            r'damaged in transit', r'pincode', r'address update', r'days and counting',
            r'stuck in transit', r'front door', r'waiting for something to show up',
            r'order status has not moved'
        ])

        has_pure_billing_intent = any(re.search(p, m) for p in [
            r'double payment', r'charged twice', r'card charged two times', r'two times',
            r'deducted twice', r'gst', r'tax bill', r'tax invoice', r'invoice with gst',
            r'download invoice', r'promo code', r'coupon code', r'discount not applied',
            r'discount code', r'cancel my order', r'please cancel', r'cancel order',
            r'ordered by mistake', r'cancellation', r'no order id', r'no orders',
            r'failed order after payment', r'amount deducted without order'
        ])

        # If pure billing intent is present without shipment delivery complaint:
        if has_pure_billing_intent and not has_delivery_intent:
            return 'Billing & Payments', 0.98, 'pure_billing_intent'

        # If delivery complaint is present (even with 'paid', 'money gone'):
        if has_delivery_intent:
            # Check if it's return pickup
            if any(x in m for x in ['return pickup', 'pickup has not', 'nobody came for pickup', 'reverse pickup']):
                return 'Returns & Refunds', 0.96, 'return_pickup_intent'
            return 'Delivery & Shipping', 0.97, 'delivery_shipping_intent'

        # 2. Return & Refund Pickup
        if any(re.search(p, m) for p in [
            r'return pickup', r'pickup has not happened', r'nobody came for pickup',
            r'pickup missed', r'pickup pending', r'reverse pickup', r'return my',
            r'pick up the', r'boy didn\'?t turn up'
        ]):
            return 'Returns & Refunds', 0.95, 'return_pickup_intent'

        # 3. Warranty & RMA claims
        if any(re.search(p, m) for p in [
            r'warranty claim', r'rma', r'claim number', r'service centre', r'service center',
            r'hardware defect', r'manufacturing defect'
        ]):
            return 'Warranty & Repair', 0.96, 'warranty_rma_intent'

        # 4. Account & Login
        if any(re.search(p, m) for p in [
            r'cannot login', r'unable to log', r'otp not', r'reset password',
            r'login issue', r'cant login'
        ]):
            return 'Account & Login', 0.95, 'account_login_intent'

        return None, 0.0, None

    def predict(self, text):
        """
        Classifies input text into one of the 11 categories.
        Returns: dict with {category, confidence, rule_matched, top_tokens}
        """
        if not text:
            return {
                'category': 'Other',
                'confidence': 0.5,
                'rule_matched': 'empty_input',
                'probabilities': {}
            }

        # 1. Check high-confidence domain intent rules
        rule_cat, rule_conf, rule_name = self._apply_domain_intent_rules(text)
        if rule_cat:
            return {
                'category': rule_cat,
                'confidence': rule_conf,
                'rule_matched': rule_name,
                'probabilities': {rule_cat: rule_conf}
            }

        # 2. Fall back to Naive Bayes probabilistic model
        if not self.is_trained:
            return {
                'category': 'Other',
                'confidence': 0.5,
                'rule_matched': 'untrained_fallback',
                'probabilities': {}
            }

        toks = tokenize(text)
        V = len(self.vocab)
        scores = {}

        for c, doc_count in self.cat_doc_counts.items():
            log_prior = math.log(doc_count / self.num_docs)
            log_likelihood = 0.0
            tot_w = self.cat_total_words[c] + self.alpha * V
            for t in toks:
                w_cnt = self.cat_word_counts[c].get(t, 0)
                log_likelihood += math.log((w_cnt + self.alpha) / tot_w)
            scores[c] = log_prior + log_likelihood

        # Softmax normalization for calibrated confidence
        max_score = max(scores.values())
        exp_scores = {c: math.exp(s - max_score) for c, s in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {c: round(exp_s / sum_exp, 4) for c, exp_s in exp_scores.items()}

        best_cat = max(probs.keys(), key=lambda c: probs[c])
        best_conf = probs[best_cat]

        return {
            'category': best_cat,
            'confidence': best_conf,
            'rule_matched': 'naive_bayes_nlp',
            'probabilities': probs
        }
