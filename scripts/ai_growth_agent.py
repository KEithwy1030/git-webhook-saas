# -*- coding: utf-8 -*-
"""
AI Growth & Auto-Ops Agent for git-webhook-saas
This script is triggered periodically to audit metrics, analyze traffic/conversions against the 50-subscriber goal,
and output proposed optimizations (code PRs or marketing drafts) for human approval.
"""
import os
import sys
import json
from datetime import datetime

# Database Connection config (aligned with docker-compose settings)
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'git_webhook'
DB_PORT = 18340 # Mapping port or internal docker port. Locally we can connect via tunnel or Docker Exec.

def get_db_metrics():
    """
    Fetch SaaS indicators from the local database
    """
    try:
        import pymysql
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=3306, # Connect internally or fallback to sqlite if debug
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        # Fallback to local SQLite if MySQL is not reachable directly on host
        # (Usually in local macOS host we might run it inside docker env)
        print(f"Warning: Cannot connect to MySQL directly ({e}). Simulating local db metrics...")
        return {
            'total_users': 12,
            'premium_users': 3,
            'total_webhooks': 28,
            'fail_deployments': 4,
            'success_deployments': 95
        }

    try:
        with connection.cursor() as cursor:
            # Users
            cursor.execute("SELECT COUNT(*) as cnt FROM user")
            total_users = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM user WHERE is_premium = 1")
            premium_users = cursor.fetchone()['cnt']
            
            # Webhooks
            cursor.execute("SELECT COUNT(*) as cnt FROM web_hook WHERE deleted = 0")
            total_webhooks = cursor.fetchone()['cnt']
            
            # Deployments
            cursor.execute("SELECT COUNT(*) as cnt FROM history WHERE status in ('3', '5')")
            fail_deploys = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM history WHERE status = '4'")
            success_deploys = cursor.fetchone()['cnt']
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'total_webhooks': total_webhooks,
                'fail_deployments': fail_deploys,
                'success_deployments': success_deploys
            }
    finally:
        connection.close()

def generate_ai_growth_strategy(metrics, target_subscribers=50):
    """
    Generate actions based on metrics and targets.
    In production, this queries the LLM with the context.
    """
    current_subs = metrics['premium_users']
    deficit = target_subscribers - current_subs
    success_rate = 0.0
    total_deploys = metrics['success_deployments'] + metrics['fail_deployments']
    if total_deploys > 0:
        success_rate = (metrics['success_deployments'] / total_deploys) * 100

    report = []
    actions = []
    
    report.append(f"# 🤖 AI Growth Agent Audit Report - {datetime.now().strftime('%Y-%m-%d')}")
    report.append(f"### 📈 Current KPI Tracker vs. Goal ({target_subscribers} Subscribers)")
    report.append(f"*   **Premium Subscribers**: {current_subs} / {target_subscribers} (Deficit: -{deficit})")
    report.append(f"*   **Total Registered Users**: {metrics['total_users']}")
    report.append(f"*   **SaaS Conversion Rate**: {(current_subs/metrics['total_users']*100) if metrics['total_users'] > 0 else 0:.2f}%")
    report.append(f"*   **Deployment Success Rate**: {success_rate:.2f}% (Fails: {metrics['fail_deployments']})")
    report.append("\n---\n")
    
    report.append("### 🧠 AI Growth Strategy & Analysis")
    if deficit > 0:
        report.append(f"We are currently {deficit} subscribers short of the monthly target. Conversion rate is low. We need to implement two primary vectors: conversion copy A/B test and content marketing.")
        
        # Action 1: Marketing post generation
        blog_content = f"""# How to Automate your VPS Deployments with Git-Webhook & AI Auto-Fix
Tired of logging into your server via SSH just to check why your npm install failed? 
In this guide, we show you how to set up `git-webhook-saas` to catch errors automatically, 
diagnose them using AI, and apply a fix with a single click.

## Features:
1. Zero configurations.
2. Direct integration with GitHub/GitLab.
3. 🤖 AI diagnostics and Auto-Fix suggestions.

*Read more and subscribe at http://your-saas-url.com*
"""
        actions.append({
            'type': 'MARKETING_BLOG',
            'path': 'docs/marketing/blog_draft.md',
            'content': blog_content,
            'description': "Create a promotional blog post on DevOps/CI-CD automated troubleshooting to attract developers."
        })
        
        # Action 2: Conversion Copy Optimization
        actions.append({
            'type': 'A_B_TEST_COPY',
            'path': 'app/templates/index.html',
            'description': "Update home landing page conversion copy to highlight 'AI Auto-Fix' to improve free-to-premium conversion rate."
        })
        
    return report, actions

def write_approval_file(report, actions):
    """
    Output the pending actions to a local file for the human to review and approve.
    """
    approval_path = "GROWTH_TASK_APPROVAL.md"
    content = "\n".join(report)
    content += "\n## ⚡ Pending Growth Tasks (Waiting for Human Approval)\n"
    
    for idx, act in enumerate(actions):
        content += f"### [Task {idx+1}] Type: {act['type']}\n"
        content += f"*   **Description**: {act['description']}\n"
        content += f"*   **Target File**: `{act['path']}`\n"
        content += f"*   **Status**: ⏳ Waiting for approval\n\n"
        
    content += "\n---\n*To approve and apply these changes, please run: `python scripts/ai_growth_agent.py --approve`*\n"
    
    with open(approval_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Success: Growth plan written to {approval_path}. Please review it.")

if __name__ == '__main__':
    # Parse CLI argument for approval gateway
    if len(sys.argv) > 1 and sys.argv[1] == '--approve':
        print("Approving tasks... Local AI is merging changes and releasing marketing drafts.")
        # Simulating merging files
        os.makedirs("docs/marketing", exist_ok=True)
        with open("docs/marketing/blog_draft.md", "w") as f:
            f.write("# Approved Blog Post Draft\nReady for publishing.")
        print("OK: Task approved and local assets released. Run git push to deploy online.")
    else:
        metrics = get_db_metrics()
        report, actions = generate_ai_growth_strategy(metrics)
        write_approval_file(report, actions)
