# -*- coding: utf-8 -*-
import re

def analyze_error_log(log_text):
    """
    Analyze build/deploy stderr logs and return root cause analysis and a bash fix script.
    """
    if not log_text:
        return {
            'analysis': "AI Report: Empty execution logs. No failure detected in stderr.",
            'fix_suggestion': ""
        }
        
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
