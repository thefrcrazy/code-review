#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
import ssl
import time
import datetime
import re
import argparse
import threading
import itertools

# --- COLORS & UI ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*40}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {msg} {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*40}{Colors.ENDC}\n")

def print_step(step, msg):
    print(f"{Colors.BLUE}{Colors.BOLD}[{step}]{Colors.ENDC} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}{Colors.BOLD}✔ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✖ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.ENDC}")

# --- CONFIGURATION ---
CHUNK_SIZE = 200 * 1024    # 200 Ko par chunk pour l'API
DELAY_BETWEEN_CHUNKS = 2   # Pause de 2 secondes entre les appels pour éviter le rate limit

IGNORED_DIRS = {
    "node_modules", ".git", ".DS_Store", "dist", "build", "__pycache__", 
    ".venv", "venv", ".next", ".turbo", ".cache", "target", ".idea", ".vscode",
    "public", "assets", "vendor", "out", ".output", "coverage"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", 
    ".zip", ".tar", ".gz", ".exe", ".bin", ".pyc", ".lock", ".lockb",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".mov", ".map",
    ".db", ".sqlite", ".sqlite3"
}

def load_env():
    env_vars = {}
    # Chemins possibles pour le .env
    possible_paths = [
        os.path.join(os.getcwd(), ".env"), # Dossier où on lance la commande
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env") # Dossier du script
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
                if "MISTRAL_API_KEY" in env_vars:
                    return env_vars # On s'arrête dès qu'on a la clé
        except Exception: pass
    return env_vars


def get_project_chunks(root_path):
    chunks = []
    current_chunk = []
    current_chunk_files = []
    current_chunk_size = 0
    total_files_scanned = 0
    
    print_info(f"Analyse du dossier : {Colors.BOLD}{root_path}{Colors.ENDC}")
    
    if not os.path.isdir(root_path):
        print_error(f"{root_path} n'est pas un dossier valide.")
        return []

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
        
        for file in files:
            total_files_scanned += 1
            if file.startswith('.') or any(file.endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue
            
            if file in {"package-lock.json", "bun.lockb", "yarn.lock", "pnpm-lock.yaml", "GUARD.md"}:
                continue

            full_path = os.path.join(root, file)
            
            try:
                if os.path.islink(full_path): continue
                
                file_size = os.path.getsize(full_path)
                # Logging des gros fichiers
                if file_size > 10 * 1024 * 1024: 
                    print_warning(f"Fichier volumineux inclus : {file} ({file_size/1024/1024:.1f} Mo)")

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if not content or "\0" in content: continue
                        
                    rel_path = os.path.relpath(full_path, root_path)
                    entry = f"\n--- FICHIER : {rel_path} ---\n{content}\n"
                    entry_size = len(entry.encode('utf-8'))
                    
                    if current_chunk_size + entry_size > CHUNK_SIZE and current_chunk:
                        chunks.append(("".join(current_chunk), current_chunk_files))
                        current_chunk = []
                        current_chunk_files = []
                        current_chunk_size = 0
                    
                    current_chunk.append(entry)
                    current_chunk_files.append(rel_path)
                    current_chunk_size += entry_size
                    
                    # Petit feedback visuel discret pendant le scan
                    if total_files_scanned % 50 == 0:
                        sys.stdout.write(f"\r{Colors.CYAN}Scanné {total_files_scanned} fichiers...{Colors.ENDC}")
                        sys.stdout.flush()
                    
            except Exception as e:
                print_error(f"Erreur lecture {file}: {e}")
                continue
    
    sys.stdout.write("\r" + " " * 50 + "\r") # Effacer la ligne de progression du scan

    # Ajouter le dernier chunk
    if current_chunk:
        chunks.append(("".join(current_chunk), current_chunk_files))

    return chunks

def call_codestral(api_key, api_url, content, prompt):
    # print(f"Envoi à Codestral ({len(context)/1024:.1f} Ko)...") # Géré par le main loop pour l'affichage
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": "Tu es un expert en code. Analyse les fichiers fournis et réponds en français. Sois concis et précis."},
            {"role": "user", "content": f"Voici une partie des fichiers du projet :\n{content}\n\nINSTRUCTION : {prompt}"}
        ],
        "temperature": 0
    }
    
    req = urllib.request.Request(api_url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    try:
        context_ssl = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context_ssl) as response:
            res = json.loads(response.read().decode())
            return res['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        raise Exception(f"Erreur API {e.code}: {error_msg}")

def call_codestral_summary(api_key, api_url, previous_responses, prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    summary_context = "Voici les analyses partielles reçues précédemment :\n\n"
    for i, resp in enumerate(previous_responses):
        summary_context += f"--- PARTIE {i+1} ---\n{resp}\n\n"
        
    data = {
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": "Tu es un lead developer. Ton but est de synthétiser plusieurs analyses partielles de code en un rapport global cohérent."},
            {"role": "user", "content": f"{summary_context}\n\nTACHE FINALE : {prompt}\nFais une synthèse globale, élimine les redondances et structure la réponse."}
        ],
        "temperature": 0
    }
    
    req = urllib.request.Request(api_url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    try:
        context_ssl = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context_ssl) as response:
            res = json.loads(response.read().decode())
            return res['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        raise Exception(f"Erreur API de synthèse {e.code}: {error_msg}")

class Spinner:
    def __init__(self, message="Traitement en cours...", delay=0.1):
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.delay = delay
        self.busy = False
        self.spinner_visible = False
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None

    def run(self):
        while not self.stop_event.is_set():
            sys.stdout.write(f"\r{Colors.BLUE}{next(self.spinner)} {self.message}{Colors.ENDC}   ")
            sys.stdout.flush()
            time.sleep(self.delay)

    def start(self):
        self.busy = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

def colorize_markdown(text):
    # Headers
    text = re.sub(r'^(#+ .*)$', f'{Colors.HEADER}{Colors.BOLD}\\1{Colors.ENDC}', text, flags=re.MULTILINE)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', f'{Colors.WARNING}{Colors.BOLD}\\1{Colors.ENDC}', text)
    # Inline code
    text = re.sub(r'`(.*?)`', f'{Colors.CYAN}\\1{Colors.ENDC}', text)
    # Bullet points
    text = re.sub(r'^(\s*[•\-\*] )', f'{Colors.BLUE}\\1{Colors.ENDC}', text, flags=re.MULTILINE)
    return text

def save_report(target, prompt, content):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = os.path.basename(os.path.abspath(target))
    # On force la création à la racine de l'exécution actuelle
    reviews_dir = os.path.join(os.getcwd(), "reviews")
    
    if not os.path.exists(reviews_dir):
        os.makedirs(reviews_dir)
        
    filename = f"report_{project_name}_{timestamp}.md"
    file_path = os.path.join(reviews_dir, filename)
    
    report_content = f"# Rapport d'analyse Code\n"
    report_content += f"**Date** : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    report_content += f"**Cible** : `{target}`\n"
    if prompt:
        report_content += f"**Instruction** : {prompt}\n"
    report_content += "\n---\n\n"
    report_content += content
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return file_path

if __name__ == "__main__":
    print_header("REVIEW CODE ANALYZER")
    
    env = load_env()
    # Priorité : Variable d'environnement système > Fichier .env
    api_key = os.environ.get("MISTRAL_API_KEY") or env.get("MISTRAL_API_KEY")
    api_url = os.environ.get("CODESTRAL_URL") or env.get("CODESTRAL_URL", "https://codestral.mistral.ai/v1/chat/completions")

    if not api_key:
        print_error("MISTRAL_API_KEY non trouvée.")
        print_info("Solutions :")
        print_info(f"1. Obtenez une clé ici : {Colors.BOLD}https://console.mistral.ai/codestral{Colors.ENDC}")
        print_info(f"2. Ajoutez la clé dans : {Colors.BOLD}{os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')}{Colors.ENDC}")
        print_info(f"3. OU exportez la variable : {Colors.BOLD}export MISTRAL_API_KEY='votre_cle'{Colors.ENDC}")
        sys.exit(1)

    # --- ARGUMENT PARSING ---
    parser = argparse.ArgumentParser(description="Analyseur de code via IA (Codestral).")
    parser.add_argument("target", nargs='?', default=".", help="Dossier ou fichier à analyser")
    parser.add_argument("prompt", nargs='?', default=None, help="Instruction spécifique pour l'IA")
    parser.add_argument("-l", "--lang", help="Langue de la réponse (ex: 'English', 'Spanish')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Afficher tous les fichiers analysés")
    parser.add_argument("--uninstall", action="store_true", help="Désinstaller l'outil")
    
    args = parser.parse_args()
    
    # Gestion de la désinstallation
    if args.uninstall:
        install_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install.sh")
        if os.path.exists(install_script):
            os.execv("/bin/bash", ["/bin/bash", install_script, "--uninstall"])
        else:
            print_error("Script d'installation introuvable pour la désinstallation.")
            sys.exit(1)

    target = args.target
    
    # Gestion du prompt via GUARD.md
    guard_path = os.path.join(os.path.abspath(target), "GUARD.md")
    base_prompt = "Fais une analyse globale et cherche des bugs."
    
    if os.path.exists("GUARD.md"):
         with open("GUARD.md", "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
            print_info(f"Utilisation de GUARD.md local comme instruction ({len(base_prompt)} cars).")
    elif os.path.exists(guard_path):
         with open(guard_path, "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
            print_info(f"Utilisation de GUARD.md cible comme instruction ({len(base_prompt)} cars).")
            
    # Ajout du prompt utilisateur s'il existe
    if args.prompt:
        base_prompt = f"{args.prompt}\n\n--- RÈGLES À SUIVRE (GUARD.md) ---\n{base_prompt}"

    # Gestion de la langue
    if args.lang:
        lang_instruction = f"\n\nIMPORTANT : La réponse finale doit être rédigée IMPÉRATIVEMENT en {args.lang}."
        base_prompt += lang_instruction
        print_info(f"Langue forcée : {args.lang}")

    try:
        print_step("1/4", "Scan et découpage du projet...")
        spinner_scan = Spinner("Parcours des fichiers...")
        spinner_scan.start()
        chunks = get_project_chunks(os.path.abspath(target))
        spinner_scan.stop()
        
        if not chunks:
            print_warning("Aucun fichier texte pertinent trouvé ou dossier vide.")
            sys.exit(0)
            
        print_success(f"Projet découpé en {Colors.BOLD}{len(chunks)}{Colors.ENDC} partie(s) (env. {CHUNK_SIZE/1024:.0f} Ko/partie).")
        
        ai_responses = []
        
        print_step("2/4", f"Analyse par l'IA en cours ({len(chunks)} étapes)...")
        
        for i, (chunk_content, chunk_files) in enumerate(chunks):
            current_step = i + 1
            total_steps = len(chunks)
            
            # Barre de progression simple
            percent = int((current_step / total_steps) * 20)
            bar = "█" * percent + "░" * (20 - percent)
            
            lines_to_clear = 0
            print(f"\n{Colors.BLUE}┌── {Colors.BOLD}Partie {current_step}/{total_steps}{Colors.ENDC} {Colors.BLUE}[{bar}]{Colors.ENDC}")
            lines_to_clear += 2 # \n + header
            print(f"{Colors.BLUE}│{Colors.ENDC} Taille: {len(chunk_content)/1024:.1f} Ko")
            lines_to_clear += 1
            
            # Affichage amélioré des fichiers
            print(f"{Colors.BLUE}│{Colors.ENDC} Fichiers Analysés :")
            lines_to_clear += 1
            if args.verbose or len(chunk_files) <= 10:
                for f in chunk_files:
                    print(f"{Colors.BLUE}│{Colors.ENDC}   • {f}")
                    lines_to_clear += 1
            else:
                 for f in chunk_files[:8]:
                    print(f"{Colors.BLUE}│{Colors.ENDC}   • {f}")
                    lines_to_clear += 1
                 print(f"{Colors.BLUE}│{Colors.ENDC}   ... (+{len(chunk_files)-8} autres fichiers, utilisez -v pour tout voir)")
                 lines_to_clear += 1
            
            chunk_prompt = f"{base_prompt} (Ceci est la partie {i+1}/{len(chunks)} du code)."
            
            spinner = Spinner("L'IA réfléchit et analyse le code...")
            spinner.start()
            start_time = time.time()
            try:
                response = call_codestral(api_key, api_url, chunk_content, chunk_prompt)
            finally:
                spinner.stop()
            elapsed = time.time() - start_time
            
            # Effacement des lignes de détails pour un affichage propre
            for _ in range(lines_to_clear):
                sys.stdout.write("\033[F\033[K")
            sys.stdout.flush()

            ai_responses.append(response)
            print(f"{Colors.GREEN}✔{Colors.ENDC} {Colors.BOLD}Partie {current_step}/{total_steps}{Colors.ENDC} [{bar}] {Colors.CYAN}({len(chunk_content)/1024:.1f} Ko){Colors.ENDC} {Colors.GREEN}Succès ({elapsed:.1f}s){Colors.ENDC}")
            
            if i < len(chunks) - 1:
                time.sleep(DELAY_BETWEEN_CHUNKS)

        final_result = ""
        if len(chunks) == 1:
            print_step("3/4", "Affichage du résultat unique")
            print("\n" + "="*40 + "\n")
            print(colorize_markdown(ai_responses[0]))
            print("\n" + "="*40 + "\n")
            final_result = ai_responses[0]
        else:
            print_step("3/4", "Génération de la synthèse globale...")
            spinner_final = Spinner("Rédaction du rapport final...")
            spinner_final.start()
            try:
                final_summary = call_codestral_summary(api_key, api_url, ai_responses, base_prompt)
            finally:
                spinner_final.stop()
            
            print("\n") # Espace avant le header
            print_header("RÉSULTAT SYNTHÉTIQUE")
            print(colorize_markdown(final_summary))
            print("\n") # Espace après le rapport
            final_result = final_summary

        print_step("4/4", "Sauvegarde et Finalisation")
        saved_path = save_report(target, args.prompt, final_result)
        print_success(f"Rapport sauvegardé dans : {Colors.BOLD}{saved_path}{Colors.ENDC}")
        
    except Exception as e:
        print_error(f"FATAL ERROR: {e}")
        # Ensure threads are stopped
        sys.exit(1)