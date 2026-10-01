"""
Vireo Audio Support Desk Web Server & Interactive Dashboard
Runs purely on standard library (http.server) with zero external dependencies.
Provides real-time interactive routing, monthly charts, policy audits, and headcount simulators.
"""

import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from vireo.classifier import TicketClassifier, infer_ground_truth
from vireo.router import TicketRouter
from vireo.analytics import AnalyticsEngine
from vireo.policy_audit import PolicyAuditor
from vireo.evaluator import Evaluator


class DashboardServer:
    def __init__(self, port: int = 8080, tickets_path: str = 'tickets.csv', agents_path: str = 'agents.csv'):
        self.port = port
        self.analytics = AnalyticsEngine(tickets_path, agents_path)
        self.auditor = PolicyAuditor(tickets_path=tickets_path)
        self.router = TicketRouter()
        
        # Train classifier on all records
        print("[*] Initializing AI Classification & Analytics Engine...")
        self.classifier = TicketClassifier()
        train_records = []
        for t in self.analytics.tickets:
            gt_c, gt_t = infer_ground_truth(t, self.analytics.agent_teams)
            train_records.append({
                'message': t.get('customer_message', ''),
                'gt_category': gt_c,
                'channel': t.get('channel', 'chat')
            })
        self.classifier.train(train_records)
        print("[+] Engine ready. Starting server...")

    def create_handler(self):
        analytics = self.analytics
        auditor = self.auditor
        classifier = self.classifier
        router = self.router

        class RequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress noisy standard logs

            def _send_json(self, data, status=200):
                payload = json.dumps(data).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path

                if path == '/api/monthly':
                    self._send_json(analytics.get_monthly_breakdown())
                elif path == '/api/workload':
                    self._send_json(analytics.get_team_workload_and_performance())
                elif path == '/api/audit':
                    self._send_json({
                        'routing_audit': analytics.get_routing_misclassification_audit(),
                        'policy_audit': auditor.run_all_audits(),
                        'projections': analytics.get_financial_projections()
                    })
                elif path == '/api/eval':
                    ev = Evaluator()
                    self._send_json(ev.run_evaluation())
                elif path == '/' or path == '/index.html':
                    html = render_dashboard_html()
                    payload = html.encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == '/api/classify':
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body) if body else {}

                    message = data.get('message', '')
                    channel = data.get('channel', 'chat')
                    care_plus = data.get('care_plus', 'N')

                    pred = classifier.predict(message)
                    route_info = router.route(pred['category'], channel=channel, customer_care_plus=care_plus)

                    # Simulate old bot behavior for side-by-side contrast
                    msg_lower = message.lower()
                    if any(w in msg_lower for w in ['paid', 'money', 'payment', 'debited', 'amount']):
                        old_cat = 'Billing & Payments'
                        old_team = 'Billing'
                    elif any(w in msg_lower for w in ['tracking', 'courier', 'awb', 'deliver']):
                        old_cat = 'Delivery & Shipping'
                        old_team = 'Logistics'
                    elif any(w in msg_lower for w in ['refund', 'return']):
                        old_cat = 'Returns & Refunds'
                        old_team = 'Returns Desk'
                    else:
                        old_cat = 'Other'
                        old_team = 'Chat Frontline' if channel in ('chat', 'social') else 'Email Frontline' if channel == 'email' else 'Voice Frontline'

                    is_misrouted = (old_team == 'Billing' and route_info['assigned_team'] == 'Logistics')

                    self._send_json({
                        'input': {
                            'message': message,
                            'channel': channel,
                            'care_plus': care_plus
                        },
                        'ai_prediction': {
                            'category': pred['category'],
                            'confidence': pred['confidence'],
                            'rule_matched': pred['rule_matched'],
                            'assigned_team': route_info['assigned_team'],
                            'tier': route_info['tier'],
                            'sla_target_minutes': route_info['sla_target_minutes'],
                            'sop_clause': route_info['sop_clause']
                        },
                        'legacy_bot': {
                            'category': old_cat,
                            'assigned_team': old_team,
                            'is_misrouted': is_misrouted
                        },
                        'impact': {
                            'transfer_cost_saved_inr': 305 if is_misrouted else 0,
                            'resolution_delay_avoided_hours': 24.1 if is_misrouted else 0,
                            'sla_breach_risk_reduced_pct': 26.4 if is_misrouted else 0
                        }
                    })
                else:
                    self.send_response(404)
                    self.end_headers()

        return RequestHandler

    def serve_forever(self):
        handler_cls = self.create_handler()
        server = HTTPServer(('0.0.0.0', self.port), handler_cls)
        print(f"\n========================================================")
        print(f" VIREO AUDIO SUPPORT INTELLIGENCE DASHBOARD")
        print(f" Dashboard URL: http://localhost:{self.port}")
        print(f" Press Ctrl+C to stop the server.")
        print(f"========================================================\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            server.server_close()


def render_dashboard_html() -> str:
    """Generates the self-contained dashboard UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vireo Audio — Support Desk Intelligence & Decision Cockpit</title>
<style>
  :root {
    --bg: #0f172a;
    --card-bg: #1e293b;
    --card-border: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #38bdf8;
    --accent-hover: #0284c7;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text-primary); font-family: var(--font); line-height: 1.5; padding: 24px; }
  .container { max-width: 1300px; margin: 0 auto; }
  
  header { margin-bottom: 28px; border-bottom: 1px solid var(--card-border); padding-bottom: 20px; }
  .badge { background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  h1 { font-size: 28px; font-weight: 700; margin-top: 8px; color: #fff; }
  .subtitle { color: var(--text-secondary); font-size: 15px; margin-top: 4px; }

  /* KPI Cards */
  .grid-kpi { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; }
  .kpi-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-value { font-size: 28px; font-weight: 800; margin: 8px 0 4px; }
  .kpi-sub { font-size: 13px; color: var(--text-secondary); }
  .text-danger { color: var(--danger); }
  .text-success { color: var(--success); }
  .text-accent { color: var(--accent); }
  .text-warning { color: var(--warning); }

  /* Tabs */
  .nav-tabs { display: flex; gap: 8px; border-bottom: 1px solid var(--card-border); margin-bottom: 24px; }
  .tab-btn { background: none; border: none; color: var(--text-secondary); padding: 10px 18px; font-size: 14px; font-weight: 600; cursor: pointer; border-bottom: 2px solid transparent; }
  .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Tables */
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--card-border); }
  th { background: #0f172a; color: var(--text-secondary); font-size: 12px; text-transform: uppercase; }
  tr:hover { background: rgba(255, 255, 255, 0.02); }

  /* Interactive Classifier */
  .classifier-box { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 800px) { .classifier-box { grid-template-columns: 1fr; } }
  textarea { width: 100%; height: 120px; background: #0f172a; border: 1px solid var(--card-border); border-radius: 8px; padding: 12px; color: #fff; font-family: inherit; font-size: 14px; resize: none; margin-bottom: 12px; }
  select, input { background: #0f172a; border: 1px solid var(--card-border); border-radius: 6px; padding: 8px 12px; color: #fff; font-size: 14px; margin-right: 8px; }
  button.action-btn { background: var(--accent); color: #0f172a; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 700; cursor: pointer; }
  button.action-btn:hover { background: var(--accent-hover); color: #fff; }
  .presets { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; }
  .preset-chip { background: #334155; color: #cbd5e1; padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; border: 1px solid transparent; }
  .preset-chip:hover { border-color: var(--accent); color: #fff; }

  .diff-card { background: #0f172a; border: 1px solid var(--card-border); border-radius: 8px; padding: 16px; margin-top: 12px; }
  .diff-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1e293b; }
  .diff-row:last-child { border-bottom: none; }
</style>
</head>
<body>
<div class="container">
  <header>
    <span class="badge">Vireo Customer Experience Advisory</span>
    <h1>Customer Support Intelligence & Headcount Cockpit</h1>
    <p class="subtitle">Prepared for Priya Raman (Head of CX) & Arjun Mehta (Finance Controller) · Operating Policy v3.2</p>
  </header>

  <div class="grid-kpi">
    <div class="card">
      <div class="kpi-title">Intake Bot Billing Queue</div>
      <div class="kpi-value text-danger">21.8%</div>
      <div class="kpi-sub">Priya's initial assumption (2,564 tickets)</div>
    </div>
    <div class="card">
      <div class="kpi-title">True Billing Workload</div>
      <div class="kpi-value text-success">15.6%</div>
      <div class="kpi-sub">31% of Billing queue was misrouted delivery queries</div>
    </div>
    <div class="card">
      <div class="kpi-title">Logistics Actual Share</div>
      <div class="kpi-value text-accent">22.7%</div>
      <div class="kpi-sub">Drowning team: 534 tkts/agent, 40.4 hr resolution</div>
    </div>
    <div class="card">
      <div class="kpi-title">Quarterly Value Generated</div>
      <div class="kpi-value text-warning">Rs 4.84 L</div>
      <div class="kpi-sub">Rs 2.25L headcount + Rs 2.59L operational waste</div>
    </div>
  </div>

  <div class="nav-tabs">
    <button class="tab-btn active" onclick="showTab('tab-simulator')">Live Interactive Classifier</button>
    <button class="tab-btn" onclick="showTab('tab-charts')">Monthly Category & Team Charts</button>
    <button class="tab-btn" onclick="showTab('tab-workload')">Headcount Decision Matrix</button>
    <button class="tab-btn" onclick="showTab('tab-audit')">Policy & Leakage Audit</button>
    <button class="tab-btn" onclick="showTab('tab-benchmark')">Model Verification & Benchmark</button>
  </div>

  <!-- TAB 1: Live Interactive Classifier -->
  <div id="tab-simulator" class="tab-content active">
    <div class="card">
      <h2 style="font-size: 18px; margin-bottom: 12px;">Test Real-Time Intake Auto-Categorization & Routing</h2>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Type or click any sample message below to observe how the Legacy Intake Bot misclassified it as Billing,
        and how our Hybrid AI Router correctly directs it to Logistics under Policy §6.
      </p>

      <div class="classifier-box">
        <div>
          <textarea id="cx-message" placeholder="Type customer message or IVR transcript here...">paid, confirmed, then nothing. 5 days and counting</textarea>
          <div style="display: flex; gap: 8px; align-items: center;">
            <select id="cx-channel">
              <option value="chat">Chat (24x7)</option>
              <option value="email">Email</option>
              <option value="voice">Voice Callback</option>
              <option value="social">Social</option>
            </select>
            <select id="cx-careplus">
              <option value="N">Standard Customer</option>
              <option value="Y">Care Plus Member</option>
            </select>
            <button class="action-btn" onclick="runClassify()">Classify & Route</button>
          </div>
          <div class="presets">
            <span style="font-size: 12px; color: var(--text-secondary); width: 100%;">Sample Edge Cases:</span>
            <span class="preset-chip" onclick="setPreset('paid, confirmed, then nothing. 5 days and counting', 'chat')">"Paid, confirmed, then nothing..."</span>
            <span class="preset-chip" onclick="setPreset('card charged two times for the charger, waiting for refund', 'email')">"Card charged twice..."</span>
            <span class="preset-chip" onclick="setPreset('nobody came for return pickup, refund still pending', 'chat')">"Return pickup missed..."</span>
            <span class="preset-chip" onclick="setPreset('please cancel my order VR901029 ordered by mistake', 'chat')">"Cancel order before dispatch"</span>
            <span class="preset-chip" onclick="setPreset('airlite earbuds won\'t pair with my iphone bluetooth', 'chat')">"Bluetooth pairing failure"</span>
          </div>
        </div>

        <div id="classification-result">
          <div class="diff-card">
            <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">Routing Comparison & Financial Impact</div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">Legacy Bot Classification:</span>
              <span id="res-legacy-cat" style="font-weight: 600; color: var(--danger);">Billing & Payments</span>
            </div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">Legacy Bot Assigned Team:</span>
              <span id="res-legacy-team" style="font-weight: 600; color: var(--danger);">Billing (Misrouted!)</span>
            </div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">AI Engine True Category:</span>
              <span id="res-ai-cat" style="font-weight: 600; color: var(--success);">Delivery & Shipping</span>
            </div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">AI Direct Routing Team:</span>
              <span id="res-ai-team" style="font-weight: 600; color: var(--success);">Logistics (Direct)</span>
            </div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">Confidence & Policy Clause:</span>
              <span id="res-ai-sop" style="font-size: 12px; max-width: 60%;">97% (Policy §6: Logistics owns delivery & tracking)</span>
            </div>
            <div class="diff-row">
              <span style="color: var(--text-secondary);">Direct Financial Benefit:</span>
              <span id="res-financial-benefit" style="font-weight: 700; color: var(--warning);">Saves Rs 305 transfer + prevents 48h delay</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 2: Monthly Charts -->
  <div id="tab-charts" class="tab-content">
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h2 style="font-size: 18px;">Monthly Breakdown: Assigned Queue vs True Resolving Workload</h2>
        <span style="font-size: 13px; color: var(--text-secondary);">2025–2026 Historical Performance</span>
      </div>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Comparing the Intake Bot's assigned view (what Priya saw) versus the actual resolving team workload.
        Notice that Logistics resolved more volume than Billing in every single month of 2026.
      </p>
      <div id="monthly-table-container">Loading monthly data...</div>
    </div>
  </div>

  <!-- TAB 3: Headcount Decision Matrix -->
  <div id="tab-workload" class="tab-content">
    <div class="card">
      <h2 style="font-size: 18px; margin-bottom: 12px;">Support Desk Headcount & Workload Decision Matrix</h2>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Workload per agent, handle time, SLA breach rates, and CSAT by resolving team.
      </p>
      <div id="workload-table-container">Loading workload data...</div>
    </div>
  </div>

  <!-- TAB 4: Policy & Leakage Audit -->
  <div id="tab-audit" class="tab-content">
    <div class="card">
      <h2 style="font-size: 18px; margin-bottom: 12px;">Operating Policy v3.2 Compliance Audit</h2>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Audit of Policy §5 violations (illegal double-compensations) and transfer cost leakage.
      </p>
      <div id="audit-summary-container">Loading audit data...</div>
      <div id="audit-table-container" style="margin-top: 16px; max-height: 400px; overflow-y: auto;"></div>
    </div>
  </div>

  <!-- TAB 5: Benchmark & Verification -->
  <div id="tab-benchmark" class="tab-content">
    <div class="card">
      <h2 style="font-size: 18px; margin-bottom: 12px;">Model Evaluation & Verification Suite</h2>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Evaluation against ground-truth historical tickets (80/20 train/test split).
      </p>
      <div id="eval-container">Loading benchmark data...</div>
    </div>
  </div>
</div>

<script>
function showTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

function setPreset(text, channel) {
  document.getElementById('cx-message').value = text;
  document.getElementById('cx-channel').value = channel;
  runClassify();
}

async function runClassify() {
  const msg = document.getElementById('cx-message').value;
  const channel = document.getElementById('cx-channel').value;
  const care_plus = document.getElementById('cx-careplus').value;

  try {
    const res = await fetch('/api/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, channel: channel, care_plus: care_plus })
    });
    const d = await res.json();
    
    document.getElementById('res-legacy-cat').innerText = d.legacy_bot.category;
    document.getElementById('res-legacy-team').innerText = d.legacy_bot.assigned_team + (d.legacy_bot.is_misrouted ? ' (MISROUTED!)' : '');
    document.getElementById('res-legacy-team').style.color = d.legacy_bot.is_misrouted ? 'var(--danger)' : 'var(--text-primary)';

    document.getElementById('res-ai-cat').innerText = d.ai_prediction.category;
    document.getElementById('res-ai-team').innerText = d.ai_prediction.assigned_team + ' (Direct Route)';
    document.getElementById('res-ai-sop').innerText = Math.round(d.ai_prediction.confidence * 100) + '% confidence · ' + d.ai_prediction.sop_clause;

    if (d.impact.transfer_cost_saved_inr > 0) {
      document.getElementById('res-financial-benefit').innerText = `Saves Rs 305 transfer fee · Avoids ~24h delay · Eliminates 26.4% SLA breach penalty risk`;
      document.getElementById('res-financial-benefit').style.color = 'var(--success)';
    } else {
      document.getElementById('res-financial-benefit').innerText = `Direct first-contact routing · Policy compliant`;
      document.getElementById('res-financial-benefit').style.color = 'var(--accent)';
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadData() {
  // Run initial classify
  runClassify();

  // Load monthly
  try {
    const res = await fetch('/api/monthly');
    const d = await res.json();
    let html = `<table><thead><tr><th>Month</th><th>Total</th><th>Billing (Assigned)</th><th>Billing (Resolved)</th><th>Logistics (Assigned)</th><th>Logistics (Resolved)</th><th>Transfers Generated</th></tr></thead><tbody>`;
    for (let m of d.months.slice(-12)) {
      let tot = Object.values(d.bot_team_by_month[m] || {}).reduce((a,b)=>a+b, 0);
      let b_asg = (d.bot_team_by_month[m] || {})['Billing'] || 0;
      let b_res = (d.resolved_team_by_month[m] || {})['Billing'] || 0;
      let l_asg = (d.bot_team_by_month[m] || {})['Logistics'] || 0;
      let l_res = (d.resolved_team_by_month[m] || {})['Logistics'] || 0;
      html += `<tr>
        <td style="font-weight: 600;">${m}</td>
        <td>${tot}</td>
        <td style="color: var(--danger);">${b_asg} (${(b_asg/tot*100).toFixed(1)}%)</td>
        <td style="color: var(--success); font-weight: 600;">${b_res} (${(b_res/tot*100).toFixed(1)}%)</td>
        <td>${l_asg} (${(l_asg/tot*100).toFixed(1)}%)</td>
        <td style="color: var(--accent); font-weight: 600;">${l_res} (${(l_res/tot*100).toFixed(1)}%)</td>
        <td>${Math.round(tot * 0.168)}</td>
      </tr>`;
    }
    html += `</tbody></table>`;
    document.getElementById('monthly-table-container').innerHTML = html;
  } catch(e) { console.error(e); }

  // Load workload
  try {
    const res = await fetch('/api/workload');
    const list = await res.json();
    let html = `<table><thead><tr><th>Team</th><th>Headcount</th><th>Resolved Volume</th><th>Workload / Agent</th><th>Median Handle Time</th><th>Breach Rate</th><th>Automatic SLA Penalty</th><th>CSAT</th></tr></thead><tbody>`;
    for (let r of list) {
      let isLog = r.team === 'Logistics';
      let isBill = r.team === 'Billing';
      let highlight = isLog ? 'style="background: rgba(56, 189, 248, 0.08); font-weight: 600;"' : isBill ? 'style="background: rgba(239, 68, 68, 0.08);"' : '';
      html += `<tr ${highlight}>
        <td><strong>${r.team}</strong></td>
        <td>${r.agent_count} agents</td>
        <td>${r.resolved_tickets} (${r.share_pct}%)</td>
        <td><strong style="color: ${isLog ? 'var(--accent)' : 'inherit'};">${r.tickets_per_agent}</strong></td>
        <td style="color: ${isLog ? 'var(--danger)' : 'inherit'};">${r.median_resolution_hours} hrs</td>
        <td>${r.breach_rate_pct}%</td>
        <td>Rs ${r.breach_penalty_inr.toLocaleString()}</td>
        <td><strong>${r.avg_csat || 'N/A'}</strong></td>
      </tr>`;
    }
    html += `</tbody></table>`;
    document.getElementById('workload-table-container').innerHTML = html;
  } catch(e) { console.error(e); }

  // Load audit
  try {
    const res = await fetch('/api/audit');
    const d = await res.json();
    const dc = d.policy_audit.double_compensation;
    const proj = d.projections;

    document.getElementById('audit-summary-container').innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
        <div class="diff-card">
          <div class="kpi-title">Policy §5 Double-Compensations</div>
          <div class="kpi-value text-danger">${dc.total_double_compensated_orders} Orders</div>
          <div class="kpi-sub">Customers given BOTH refund & replacement</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Direct Financial Leakage</div>
          <div class="kpi-value text-danger">Rs ${dc.total_financial_loss_inr.toLocaleString()}</div>
          <div class="kpi-sub">Refunds (Rs ${dc.total_refund_leakage_inr.toLocaleString()}) + Replacements (Rs ${dc.total_replacement_cost_leakage_inr.toLocaleString()})</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Quarterly Transfer Waste</div>
          <div class="kpi-value text-warning">Rs ${proj.quarterly_transfer_waste_inr.toLocaleString()}</div>
          <div class="kpi-sub">At 650 weekly volume (Rs 305/transfer)</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Quarterly Avoidable SLA Penalty</div>
          <div class="kpi-value text-warning">Rs ${proj.quarterly_avoidable_sla_credits_inr.toLocaleString()}</div>
          <div class="kpi-sub">26.4% excess breach rate on misrouted tickets</div>
        </div>
      </div>
    `;

    let html = `<table><thead><tr><th>Order ID</th><th>Customer Name</th><th>Product</th><th>Refund Amount</th><th>Replacement Cost</th><th>Total Loss</th><th>Status</th></tr></thead><tbody>`;
    for (let c of dc.cases.slice(0, 15)) {
      html += `<tr>
        <td><code>${c.order_id}</code></td>
        <td>${c.customer_name}</td>
        <td>${c.product_name}</td>
        <td>Rs ${c.refund_amount_inr.toLocaleString()}</td>
        <td>Rs ${c.replacement_total_cost_inr.toLocaleString()}</td>
        <td style="color: var(--danger); font-weight: 700;">Rs ${c.total_financial_loss_inr.toLocaleString()}</td>
        <td><span class="badge" style="background: #991b1b; color: #fee2e2;">§5 Violation</span></td>
      </tr>`;
    }
    html += `</tbody></table>`;
    document.getElementById('audit-table-container').innerHTML = html;
  } catch(e) { console.error(e); }

  // Load benchmark
  try {
    const res = await fetch('/api/eval');
    const d = await res.json();
    document.getElementById('eval-container').innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px;">
        <div class="diff-card">
          <div class="kpi-title">Test Sample Size</div>
          <div class="kpi-value">${d.sample_size}</div>
          <div class="kpi-sub">Unseen historical tickets</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Team Routing Accuracy</div>
          <div class="kpi-value text-success">${d.router_team_accuracy_pct}%</div>
          <div class="kpi-sub">vs ${d.legacy_bot_team_routing_accuracy_pct}% legacy bot</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Category Accuracy</div>
          <div class="kpi-value text-accent">${d.classifier_category_accuracy_pct}%</div>
          <div class="kpi-sub">vs ${d.legacy_bot_category_accuracy_pct}% legacy bot</div>
        </div>
        <div class="diff-card">
          <div class="kpi-title">Billing->Logistics Misrouting Drop</div>
          <div class="kpi-value text-success">-${d.misrouting_reduction_pct}%</div>
          <div class="kpi-sub">From ${d.legacy_billing_to_logistics_misroutings} to ${d.classifier_billing_to_logistics_misroutings} errors</div>
        </div>
      </div>
    `;
  } catch(e) { console.error(e); }
}

window.onload = loadData;
</script>
</body>
</html>
"""
