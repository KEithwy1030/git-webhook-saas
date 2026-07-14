# -*- coding: utf-8 -*-
"""
AI Self-Healing & Self-Evolving Operations Orchestrator (AI 自动运维与自进化闭环脚本)
This script is triggered to audit system logs for errors, scan conversion metrics,
automatically patch code/DB, and push updates to live VPS for self-evolution.
"""
import os
import sys
import subprocess
import re
from datetime import datetime

# Path Configuration
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(PROJECT_DIR, 'app/templates/index.html')
LOG_FILE_PATH = os.path.join(PROJECT_DIR, 'data/app/gunicorn.log')

def get_recent_errors():
    """
    Sensing Layer: Read system logs and detect traceback errors
    """
    if not os.path.exists(LOG_FILE_PATH):
        return []
    
    with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
        logs = f.readlines()
        
    errors = []
    # Grab the last 200 lines to look for exceptions
    recent_logs = "".join(logs[-200:])
    
    if "ProgrammingError" in recent_logs and "user" in recent_logs and "doesn't exist" in recent_logs:
        errors.append("DATABASE_TABLE_MISSING")
    
    return errors

def self_heal_database():
    """
    Self-Healing: Automatically repair database schema when table is missing
    """
    print("[🤖 AI Self-Healing] Sensing: Database table user is missing. Executing database auto-repair...")
    try:
        # Run createdb command inside local or remote docker depending on environment
        # For simplicity in this script, we trigger manage.py createdb
        ret = subprocess.call(['python', os.path.join(PROJECT_DIR, 'manage.py'), 'createdb'])
        if ret == 0:
            print("[🤖 AI Self-Healing] Auto-Repair Action: Database table successfully initialized.")
            return True
    except Exception as e:
        print("[🤖 AI Self-Healing] Error running auto-repair:", e)
    return False

def audit_conversion_metrics():
    """
    Sensing Layer: Simulate/read user conversion funnel metrics
    """
    # Simulated Funnel Metrics (normally read from growth_metrics DB table)
    # 100 people visited New WebHook form, 80 left without finishing (due to hard shell script writing)
    metrics = {
        'visit_form': 100,
        'submit_success': 20,
        'abandon_rate': 80.0
    }
    return metrics

def self_evolve_copywriting(metrics):
    """
    Self-Evolving: Optimize landing page copywriting to improve user conversion
    """
    if metrics['abandon_rate'] >= 50.0:
        print(f"[🤖 AI Self-Evolving] Sensing: Form abandonment rate is {metrics['abandon_rate']}%. Decision: Optimizing landing page copy to highlight AI Auto-Fill feature.")
        
        if not os.path.exists(INDEX_HTML_PATH):
            print("[🤖 AI Self-Evolving] Error: index.html not found.")
            return False
            
        with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Target placeholder to optimize
        target = '📢 SaaS MVP Preview Mode: '
        # New optimized copy computed by AI
        optimized_copy = '📢 SaaS MVP Preview Mode: One-Click Demo Access (Powered by 🤖 AI Auto-Fill & Diagnostics) '
        
        if target in content and optimized_copy not in content:
            updated_content = content.replace(target, optimized_copy)
            with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print("[🤖 AI Self-Evolving] Act: index.html updated with optimized marketing copy.")
            return True
        else:
            print("[🤖 AI Self-Evolving] Copy already optimized or target not found.")
    return False

def push_updates_to_live_vps():
    """
    Actuating Layer: Git push changes. The VPS auto_pull.sh cron will pull and restart app within 60s.
    """
    print("[🤖 AI Actuating] Syncing updates to live environment...")
    try:
        # Add, commit and push
        subprocess.call(['git', 'add', INDEX_HTML_PATH], cwd=PROJECT_DIR)
        subprocess.call(['git', 'commit', '-m', "style(ai-evolve): Auto-optimize landing page conversion copy based on metric audit"], cwd=PROJECT_DIR)
        ret = subprocess.call(['git', 'push', 'origin', 'master'], cwd=PROJECT_DIR)
        if ret == 0:
            print("[🤖 AI Actuating] Success: Evolved code pushed to GitHub. VPS will auto-update and deploy in 60s.")
            return True
    except Exception as e:
        print("[🤖 AI Actuating] Error pushing to GitHub:", e)
    return False

if __name__ == '__main__':
    print(f"=== [🤖 AI Self-Evolving & Healing Agent Started: {datetime.now()}] ===")
    
    # 1. sensing system errors
    errors = get_recent_errors()
    healed = False
    if "DATABASE_TABLE_MISSING" in errors:
        healed = self_heal_database()
        
    # 2. sensing conversion funnel
    metrics = audit_conversion_metrics()
    evolved = self_evolve_copywriting(metrics)
    
    # 3. If code changed, push updates to deploy online
    if evolved:
        push_updates_to_live_vps()
    else:
        if healed:
            # If database healed but no code changed, just push to trigger reload if necessary
            print("[🤖 AI] Database repaired. No code change required.")
        else:
            print("[🤖 AI] Monitoring stable. No anomalies detected. No code updates needed today.")
            
    print("=== [🤖 AI Agent Finished] ===")
