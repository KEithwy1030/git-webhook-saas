# -*- coding: utf-8 -*-
import re
import requests
import json
from app import app

def call_gemini_api(log_text):
    api_key = app.config.get('GEMINI_API_KEY', '')
    if not api_key:
        return None

    # Gemini 3.5 Flash is the latest agentic & coding flagship model.
    # Fallback to proven models sequentially to guarantee high availability.
    models_to_try = [
        "gemini-3.5-flash", 
        "gemini-1.5-flash", 
        "gemini-2.5-flash-native-audio-latest"
    ]
    
    prompt = (
        "You are a DevOps expert assistant. Analyze the following stderr execution logs and output two JSON keys:\n"
        "1. 'analysis': A short summary explaining what went wrong (MUST be written in Chinese).\n"
        "2. 'fix_suggestion': A precise bash script (or empty if not applicable) to repair the issue.\n\n"
        f"Logs:\n{log_text}\n\n"
        "Return ONLY a raw JSON object. Do NOT wrap it in ```json markdown codeblocks."
    )
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                output_text = res_data['candidates'][0]['content']['parts'][0]['text']
                
                output_text = output_text.strip()
                if output_text.startswith("```json"):
                    output_text = output_text[7:]
                elif output_text.startswith("```"):
                    output_text = output_text[3:]
                if output_text.endswith("```"):
                    output_text = output_text[:-3]
                output_text = output_text.strip()
                
                parsed = json.loads(output_text)
                print(f"[AI Diagnostic] Successfully used model: {model_name}")
                return {
                    'analysis': parsed.get('analysis', ''),
                    'fix_suggestion': parsed.get('fix_suggestion', '')
                }
        except Exception as e:
            print(f"[AI Diagnostic] Tried {model_name} failed: {e}")
            continue
    return None


def analyze_error_log(log_text):
    """
    Analyze build/deploy stderr logs and return root cause analysis and a bash fix script.
    """
    if not log_text:
        return {
            'analysis': "AI Report: Empty execution logs. No failure detected in stderr.",
            'fix_suggestion': ""
        }
        
    # Attempt to query Gemini API first
    gemini_result = call_gemini_api(log_text)
    if gemini_result:
        return gemini_result
        
    # Fallback to local regex rule-based engine
    log_text_str = str(log_text)
    analysis = "🚨 AI Diagnostic: Unknown build/deployment failure. Please check host OS logs or connection timeout."
    fix_suggestion = ""
    
    # 1. Permission Denied
    if re.search(r'(permission denied|unauthorized|failed to create directory|EACCES)', log_text_str, re.I):
        analysis = "🚨 AI Diagnostic: Deployment failed due to [Permission Denied]. The deploy user does not have write access to the target path."
        fix_suggestion = "# Elevate privileges for the build directory\nsudo chmod -R 775 . && sudo chown -R $USER:$USER ."
        
    # 2. Port conflict
    elif re.search(r'(address already in use|port \d+ already in use|EADDRINUSE)', log_text_str, re.I):
        port_match = re.search(r'port (\d+)', log_text_str, re.I)
        port = port_match.group(1) if port_match else "8080"
        analysis = f"🚨 AI Diagnostic: Port conflict detected. Target port {port} is already occupied by another running process."
        fix_suggestion = f"# Kill the process holding port {port}\nsudo kill -9 $(sudo lsof -t -i:{port}) || true"

    # 3. NPM package installation fail
    elif re.search(r'(npm ERR!|yarn error|npm install failed|ERR_RESOLVE_DEPTH)', log_text_str, re.I):
        analysis = "🚨 AI Diagnostic: NPM install command failed. This is usually caused by lockfile conflicts or network timeouts."
        fix_suggestion = "# Clear cache, delete locks and install using mirror registry\nrm -rf node_modules package-lock.json && npm install --registry=https://registry.npmmirror.com"

    # 4. Missing python module
    elif re.search(r'(ModuleNotFoundError|No module named|ImportError)', log_text_str, re.I):
        module_match = re.search(r"No module named ['\"]?(\w+)['\"]?", log_text_str, re.I)
        module = module_match.group(1) if module_match else "packages"
        analysis = f"🚨 AI Diagnostic: Missing Python package [{module}] required by the startup script."
        fix_suggestion = f"# Install the missing python module\npip install {module} --upgrade"
        
    # 5. Disk space full
    elif re.search(r'(no space left on device|disk full)', log_text_str, re.I):
        analysis = "🚨 AI Diagnostic: Target server ran out of disk space (Disk Full). Cannot write build assets."
        fix_suggestion = "# Free up disk space by pruning docker objects\ndocker system prune -af --volumes || sudo apt-get clean"

    return {
        'analysis': analysis,
        'fix_suggestion': fix_suggestion
    }
