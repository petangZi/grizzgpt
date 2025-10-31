import subprocess
import shlex

def run_scan(target, mode="vuln"):
    if mode == "vuln":
        args = [
            "nmap",
            "-Pn",
            "-sV",
            "--script=vuln,http-title,ssl-enum-ciphers",
            "-p80,443",
            "-T4",
            target
        ]
    else:
        args = [
            "nmap",
            "-Pn",
            "-sV",
            "-p80,443",
            "-T4",
            target
        ]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Scan timeout after 120 seconds"
    except Exception as e:
        return str(e)