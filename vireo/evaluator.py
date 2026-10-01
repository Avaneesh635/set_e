"""
Vireo Audio Support Ticket Evaluator & Verification Suite
Benchmarks the hybrid classifier and router against ground-truth historical tickets.
Generates accuracy, precision, recall, F1, confusion matrices, and error failure mode analyses.
"""

import csv
import random
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple

from vireo.classifier import TicketClassifier, infer_ground_truth, CATEGORIES
from vireo.router import TicketRouter


class Evaluator:
    """
    Evaluates classification and routing accuracy against ground-truth data.
    """

    def __init__(self, tickets_path: str = 'tickets.csv', agents_path: str = 'agents.csv'):
        self.tickets_path = tickets_path
        self.agents_path = agents_path
        self.tickets = []
        self.agents = {}
        self.agent_teams = {}
        self.dataset = []
        self.router = TicketRouter()
        self._load_and_prepare()

    def _load_and_prepare(self):
        with open(self.agents_path, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                self.agents[r['agent_id']] = r
                self.agent_teams[r['agent_id']] = r['team']

        with open(self.tickets_path, 'r', encoding='utf-8') as f:
            self.tickets = list(csv.DictReader(f))

        for t in self.tickets:
            gt_cat, gt_team = infer_ground_truth(t, self.agent_teams)
            self.dataset.append({
                'ticket_id': t['ticket_id'],
                'message': t['customer_message'],
                'channel': t['channel'],
                'bot_category': t['category'],
                'bot_team': t['assigned_team'],
                'gt_category': gt_cat,
                'gt_team': gt_team,
                'care_plus': 'N'  # default
            })

    def run_evaluation(self, test_split_ratio: float = 0.2, seed: int = 42) -> Dict[str, Any]:
        """
        Runs an 80/20 train/test evaluation (or full benchmark if ratio == 0).
        """
        data = list(self.dataset)
        random.seed(seed)
        random.shuffle(data)

        if test_split_ratio > 0:
            split_idx = int(len(data) * (1 - test_split_ratio))
            train_records = data[:split_idx]
            test_records = data[split_idx:]
        else:
            train_records = data
            test_records = data

        # Train classifier
        clf = TicketClassifier()
        clf.train(train_records)

        # Metrics trackers
        cat_tp = Counter()
        cat_fp = Counter()
        cat_fn = Counter()
        cat_support = Counter()

        team_tp = Counter()
        team_fp = Counter()
        team_fn = Counter()
        team_support = Counter()

        bot_cat_correct = 0
        bot_team_correct = 0

        clf_cat_correct = 0
        clf_team_correct = 0

        bot_billing_to_log = 0
        clf_billing_to_log = 0

        cat_confusion = defaultdict(Counter)
        team_confusion = defaultdict(Counter)

        error_samples = []

        for d in test_records:
            gt_c = d['gt_category']
            gt_t = d['gt_team']
            ch = d['channel']

            # Predict
            pred_res = clf.predict(d['message'])
            pred_c = pred_res['category']
            route_res = self.router.route(pred_c, channel=ch)
            pred_t = route_res['assigned_team']

            cat_support[gt_c] += 1
            team_support[gt_t] += 1

            cat_confusion[gt_c][pred_c] += 1
            team_confusion[gt_t][pred_t] += 1

            # Legacy bot comparison
            if d['bot_category'] == gt_c:
                bot_cat_correct += 1
            if d['bot_team'] == gt_t:
                bot_team_correct += 1
            if d['bot_team'] == 'Billing' and gt_t == 'Logistics':
                bot_billing_to_log += 1

            # Classifier performance
            if pred_c == gt_c:
                clf_cat_correct += 1
                cat_tp[gt_c] += 1
            else:
                cat_fp[pred_c] += 1
                cat_fn[gt_c] += 1
                if len(error_samples) < 50:
                    error_samples.append({
                        'ticket_id': d['ticket_id'],
                        'message': d['message'][:120],
                        'ground_truth_category': gt_c,
                        'predicted_category': pred_c,
                        'ground_truth_team': gt_t,
                        'predicted_team': pred_t,
                        'confidence': pred_res['confidence'],
                        'rule_matched': pred_res['rule_matched']
                    })

            # Router performance
            if pred_t == gt_t:
                clf_team_correct += 1
                team_tp[gt_t] += 1
            else:
                team_fp[pred_t] += 1
                team_fn[gt_t] += 1

            if pred_t == 'Billing' and gt_t == 'Logistics':
                clf_billing_to_log += 1

        n_test = len(test_records)

        # Compute per-category precision, recall, F1
        category_metrics = []
        for c in sorted(list(cat_support.keys())):
            tp = cat_tp[c]
            fp = cat_fp[c]
            fn = cat_fn[c]
            supp = cat_support[c]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            category_metrics.append({
                'category': c,
                'support': supp,
                'precision': round(prec, 3),
                'recall': round(rec, 3),
                'f1_score': round(f1, 3)
            })

        # Compute per-team precision, recall, F1
        team_metrics = []
        for tm in sorted(list(team_support.keys())):
            tp = team_tp[tm]
            fp = team_fp[tm]
            fn = team_fn[tm]
            supp = team_support[tm]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            team_metrics.append({
                'team': tm,
                'support': supp,
                'precision': round(prec, 3),
                'recall': round(rec, 3),
                'f1_score': round(f1, 3)
            })

        # Classify top failure modes
        failure_modes = Counter()
        for err in error_samples:
            mode = f"{err['ground_truth_category']} -> {err['predicted_category']}"
            failure_modes[mode] += 1

        return {
            'sample_size': n_test,
            'train_size': len(train_records),
            'legacy_bot_category_accuracy_pct': round((bot_cat_correct / n_test) * 100, 2),
            'legacy_bot_category_error_rate_pct': round(((n_test - bot_cat_correct) / n_test) * 100, 2),
            'classifier_category_accuracy_pct': round((clf_cat_correct / n_test) * 100, 2),
            'classifier_category_error_rate_pct': round(((n_test - clf_cat_correct) / n_test) * 100, 2),
            'legacy_bot_team_routing_accuracy_pct': round((bot_team_correct / n_test) * 100, 2),
            'legacy_bot_team_routing_error_rate_pct': round(((n_test - bot_team_correct) / n_test) * 100, 2),
            'router_team_accuracy_pct': round((clf_team_correct / n_test) * 100, 2),
            'router_team_error_rate_pct': round(((n_test - clf_team_correct) / n_test) * 100, 2),
            'legacy_billing_to_logistics_misroutings': bot_billing_to_log,
            'classifier_billing_to_logistics_misroutings': clf_billing_to_log,
            'misrouting_reduction_pct': round(((bot_billing_to_log - clf_billing_to_log) / bot_billing_to_log) * 100, 1) if bot_billing_to_log else 100.0,
            'category_metrics': category_metrics,
            'team_metrics': team_metrics,
            'category_confusion_matrix': {gt: dict(cat_confusion[gt]) for gt in cat_confusion},
            'top_failure_modes': [{'transition': k, 'count': v} for k, v in failure_modes.most_common(5)],
            'error_samples': error_samples[:10]
        }
