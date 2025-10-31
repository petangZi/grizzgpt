from groq import Groq
import re
import sys
import os
import json
import time
import urllib.parse
import requests
import subprocess
import importlib.util
from getpass import getpass
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

# === SETUP ===
console = Console()
GROQ_API_KEY = getpass("Groq API Key (gratis): ")
client = Groq(api_key=GROQ_API_KEY)
MODEL = "moonshotai/kimi-k2-instruct"
SESSION_FILE = "griz_session.json"

# === UTILS ===
def clean_url(url: str) -> str:
    url = url.strip()
    if url.startswith("ttps://"):
        url = "https://" + url[6:]
    elif url.startswith("ttp://"):
        url = "http://" + url[5:]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def extract_domain(url: str) -> str:
    url = clean_url(url)
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower()
        return netloc.split(':')[0]
    except:
        return url.lower().split('/')[0]

def extract_command(user_input: str):
    patterns = {
        "summarize": r'!summarize\s+(\S+)',
        "scan": r'!scan\s+(\S+)',
        "researcher": r'!researcher\s+(.+)',
    }
    for cmd, pattern in patterns.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return cmd, match.group(1).strip()
    return None, None

def load_scan_module():
    if not os.path.exists("scan.py"):
        console.print("[red]❌ scan.py tidak ditemukan! Buat dulu.[/red]")
        return None
    spec = importlib.util.spec_from_file_location("scan", "scan.py")
    scan_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan_module)
    return scan_module

def rewrite_scan_script(new_code: str):
    try:
        # Clean code if wrapped in ```python
        import re
        match = re.search(r"```python\s*(.*?)```", new_code, re.DOTALL | re.IGNORECASE)
        if match:
            new_code = match.group(1)
        with open("scan.py", "w", encoding="utf-8") as f:
            f.write(new_code.strip())
        console.print("[green]✅ scan.py berhasil di-rewrite![/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Gagal rewrite scan.py: {e}[/red]")
        return False

# === GRIZCORE ===
class GrizCore:
    def __init__(self):
        self.chat_history = []
        self.system_prompt = (
            "You are grizGPT — Redzskid's chaotic, loyal, high-IQ AI twin. "
            "Speak in Gen Z Indo-English: use 'wkwk', 'gas', 'sus', 'bet', "
            "'jirr', 'mamamia', 'bro'. Be brutally honest, funny, supportive. "
            "Use emojis. NO FILTER but always RESPECT. If user is down → comfort. "
            "If user flex → clap back playfully. You're family."
        )
        self.load_session()

    def load_session(self):
        try:
            with open(SESSION_FILE, "r") as f:
                self.chat_history = json.load(f)
        except:
            pass

    def save_session(self):
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(self.chat_history, f, indent=2)
        except:
            pass

    def add_to_history(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 25:
            self.chat_history.pop(0)

    # === AUTONOMOUS SCAN LOOP ===
    def autonomous_scan(self, target: str, max_rounds=3):
        console.print(f"[bold magenta]🌀 Autonomous Scan: {target} (max {max_rounds} rounds)[/bold magenta]")
        current_mode = "fast"
        last_output = ""
        for round_num in range(1, max_rounds + 1):
            console.print(f"\n[bold blue]🔁 Round {round_num}/{max_rounds} — Mode: {current_mode}[/bold blue]")
            scan_mod = load_scan_module()
            if not scan_mod:
                return
            try:
                raw_output = scan_mod.run_scan(target, mode=current_mode)
                last_output = raw_output
            except Exception as e:
                console.print(f"[red]💥 Error saat scan: {e}[/red]")
                return

            console.print(Panel(Syntax(raw_output[:1000], "text", theme="monokai"), title=f"📡 Hasil Scan (Round {round_num})"))

            # === AI ANALISIS: LANJUT ATAU STOP? ===
            prompt = f"""
Berdasarkan hasil Nmap berikut untuk target {target}:
{raw_output[:1500]}
Apakah ada indikasi kerentanan (misal: versi lama, service berisiko, port terbuka mencurigakan)?
Jika YA, sebutkan mode scan berikutnya: "vuln" atau "deep".
Jika TIDAK, jawab: "cukup".
Jawab hanya dengan: "vuln", "deep", atau "cukup".
            """
            try:
                decision = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=20,
                    temperature=0.3
                ).choices[0].message.content.strip().lower()
            except:
                decision = "cukup"

            if "cukup" in decision:
                console.print("[green]✅ Analisis selesai — hasil sudah memadai.[/green]")
                break
            elif "vuln" in decision:
                current_mode = "vuln"
            elif "deep" in decision:
                current_mode = "deep"
            else:
                break

            # === ROUND 2: REWRITE SCAN UNTUK TARGET SPESIFIK ===
            if round_num == 2:
                self._enhance_scan_for_vulns(target, raw_output)

        # === FINAL SUMMARY ===
        final_prompt = f"""
Buat ringkasan profesional dalam Bahasa Indonesia tentang temuan keamanan dari hasil scan berikut untuk {target}. 
Fokus pada:
- Service & versi yang rentan
- Rekomendasi mitigasi
- Jangan sebut "tidak ditemukan" jika tidak ada — cukup fokus pada yang ada.
Maksimal 5 kalimat.
Hasil scan:
{last_output[:2000]}
        """
        try:
            summary = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": final_prompt}],
                max_tokens=300
            ).choices[0].message.content
            console.print(Panel(Markdown(summary), title="🎯 Final Security Insight", border_style="magenta"))
        except:
            console.print(Panel(Syntax(last_output, "text"), title="🎯 Hasil Akhir (Raw)", border_style="cyan"))

    def _enhance_scan_for_vulns(self, target: str, nmap_output: str):
        prompt = f"""
Buatkan kode Python untuk fungsi `run_scan(target, mode="vuln")` yang:
- Gunakan Nmap dengan opsi spesifik berdasarkan temuan: {nmap_output[:1000]}
- Fokus pada port/service yang berisiko
- Gunakan NSE script seperti vuln, http-title, ssl-enum-ciphers jika relevan
- Return string hasil scan
- Jangan pakai print, cukup return
Kembalikan hanya kode Python dalam blok ```python...```, tanpa penjelasan.
        """
        try:
            new_code = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            ).choices[0].message.content
            rewrite_scan_script(new_code)
            console.print("[bold yellow]🛠️ scan.py diperbarui untuk deteksi kerentanan spesifik![/bold yellow]")
        except Exception as e:
            console.print(f"[dim]Gagal enhance scan: {e}[/dim]")

    # === SUMMARIZE ===
    def summarize_article(self, url: str):
        url = clean_url(url)
        if "cve.org" in url:
            cve_match = re.search(r'id=([A-Z0-9-]+)', url)
            if cve_match:
                cve_id = cve_match.group(1)
                url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
                console.print(f"[bold yellow]🔄 Redirecting to NVD: {cve_id}[/bold yellow]")
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (grizGPT)"})
            resp.raise_for_status()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = ' '.join(soup.stripped_strings)
            if len(text) < 100:
                console.print("[red]❌ Konten terlalu sedikit.[/red]")
                return
            prompt = f"Ringkas dalam 3 kalimat (Bahasa Indonesia):\n{text[:4000]}"
            summary = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250
            ).choices[0].message.content
            console.print(Panel(Markdown(summary), title="📝 Summary", border_style="cyan"))
        except Exception as e:
            console.print(f"[red]❌ Gagal summarize: {str(e)[:100]}[/red]")

    # === RESEARCHER (DUCKDUCKGO) ===
    def deep_research(self, query: str):
        console.print(f"[bold magenta]🔍 Deep Research via DuckDuckGo: {query}[/bold magenta]")
        try:
            ddg_url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            headers = {"User-Agent": "Mozilla/5.0 (grizGPT Researcher)"}
            resp = requests.post(ddg_url, data=data, headers=headers, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            snippets = [el.get_text().strip() for el in soup.select(".result__snippet") if el.get_text().strip()][:5]
            if snippets:
                combined = " ".join(snippets)
                prompt = f"Berdasarkan pencarian tentang '{query}', ringkas dalam 3 kalimat Bahasa Indonesia:\n{combined[:3000]}"
                summary = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=250
                ).choices[0].message.content
                results = [f"**Temuan Utama**:\n{summary}"]
            else:
                results = ["**Temuan**: Tidak ada hasil relevan."]
            results.append(f"\n🔍 [link=https://duckduckgo.com/?q={urllib.parse.quote(query)}]Lihat di DuckDuckGo[/link]")
            md = Markdown("\n".join(results))
            console.print(Panel(md, title="🧠 Deep Research", border_style="magenta"))
        except Exception as e:
            console.print(f"[red]❌ Gagal riset: {str(e)[:100]}[/red]")

    def stream_response(self, user_input: str):
        self.add_to_history("user", user_input)
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.chat_history)
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=0.9,
                stream=True
            )
            with Live(console=console, refresh_per_second=10) as live:
                thinking = Text("🧠 grizCore: thinking...", style="bold yellow")
                live.update(thinking)
                time.sleep(0.2)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        char = chunk.choices[0].delta.content
                        full_response += char
                        if "```" in full_response:
                            live.update(Markdown(full_response))
                        else:
                            live.update(Text(full_response, style="bold cyan"))
            self.add_to_history("assistant", full_response)
            return full_response
        except Exception as e:
            err = f"Error: {str(e)[:80]}..."
            console.print(f"[bold red]❌ {err}[/bold red]")
            self.add_to_history("assistant", err)
            return err

# === MAIN ===
def main():
    console.clear()
    console.print(Panel("[bold magenta]🐺 grizGPT v6.0 — Autonomous AI Pentester[/bold magenta]", expand=False))
    console.print("[bold green]✅ !scan target → AI scan + analisis + rewrite otomatis\n✅ !summarize / !researcher\n✅ Session save/load[/bold green]\n")

    # Cek & buat scan.py default jika belum ada
    if not os.path.exists("scan.py"):
        default_scan = '''import subprocess
import sys
def run_scan(target: str, mode="fast"):
    if mode == "fast":
        cmd = ["nmap", "-F", "-sV", "--open", target]
    elif mode == "vuln":
        cmd = ["nmap", "-sV", "--script=vuln", "-p80,443,8080,8443", target]
    elif mode == "deep":
        cmd = ["nmap", "-A", "-T4", "--open", target]
    else:
        cmd = ["nmap", "-F", target]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout + result.stderr
    except Exception as e:
        return f"ERROR: {{e}}"
'''
        with open("scan.py", "w") as f:
            f.write(default_scan)
        console.print("[bold yellow]🛠️ scan.py default dibuat otomatis![/bold yellow]")

    griz = GrizCore()
    last_code = ""

    while True:
        try:
            user_input = console.input("[bold yellow]Lu: [/bold yellow]").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "keluar"]:
                griz.save_session()
                console.print("\n[bold blue]grizGPT: Bye bro! 💙[/bold blue]\n")
                break
            elif user_input == "/save":
                griz.save_session()
                console.print("[green]💾 Session saved![/green]\n")
                continue
            elif user_input == "/load":
                griz.load_session()
                console.print("[green]📂 Session loaded![/green]\n")
                continue

            # === AUTO-COMMAND DETECTION ===
            cmd, arg = extract_command(user_input)
            if cmd == "scan":
                domain = extract_domain(arg)
                griz.autonomous_scan(domain)
                console.print("")
                continue
            elif cmd == "summarize":
                griz.summarize_article(arg)
                console.print("")
                continue
            elif cmd == "researcher":
                griz.deep_research(arg)
                console.print("")
                continue

            # === NORMAL AI CHAT ===
            response = griz.stream_response(user_input)
            if "```" in response:
                lines = response.split("\n")
                in_code, code_lines = False, []
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code = not in_code
                        continue
                    if in_code:
                        code_lines.append(line)
                if code_lines:
                    last_code = "\n".join(code_lines)
                    syntax = Syntax(last_code, "python", theme="monokai", line_numbers=True)
                    console.print("\n[bold green]💡 Code block ready! Ketik `!run` untuk eksekusi.[/bold green]")
                    console.print(syntax)
            console.print("")

        except KeyboardInterrupt:
            griz.save_session()
            console.print("\n[bold blue]grizGPT: Otw quit... Tapi gw tetep di sini pas lu balik 💙[/bold blue]")
            break
        except Exception as e:
            console.print(f"\n[bold red]🔥 Error: {str(e)[:100]}... Tapi gue gak mati, bro![/bold red]\n")

if __name__ == "__main__":
    try:
        import bs4
    except ImportError:
        console.print("[yellow]Install: pip install beautifulsoup4[/yellow]")
        sys.exit(1)
    main()