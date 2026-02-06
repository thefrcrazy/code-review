# 🔍 Code Review CLI

Un outil en ligne de commande puissant pour analyser instantanément n'importe quel codebase via l'IA de Mistral (Codestral). Il découpe intelligemment les gros projets, fournit une analyse en temps réel dans le terminal avec des couleurs, et génère des rapports Markdown détaillés.

## ✨ Fonctionnalités

- 🚀 **Analyse Multi-Parties** : Découpe automatiquement les projets volumineux pour respecter les limites de contexte.
- 🎨 **UI Terminal Dynamique** : Barres de progression, spinners et rendu Markdown colorisé directement dans votre console.
- 🛡️ **Support GUARD.md** : Personnalisez les instructions d'analyse par projet (ex: focus sécurité, performance, ou style de code).
- 📂 **Rapports Automatiques** : Sauvegarde un rapport horodaté dans un dossier `reviews/` à la racine de votre répertoire d'exécution.
- 🌍 **Support Multilingue** : Forcez la réponse dans la langue de votre choix avec l'option `-l`.
- ⚡ **Ultra Léger** : Aucune dépendance externe lourde (utilise uniquement les bibliothèques standards Python).

## 🚀 Installation

### Méthode Automatique (Recommandée)

**Sur macOS / Linux :**
```bash
curl -sSL https://raw.githubusercontent.com/thefrcrazy/code-review/main/install.sh | bash
```

**Sur Windows (PowerShell) :**
```powershell
iwr https://raw.githubusercontent.com/thefrcrazy/code-review/main/install.ps1 -useb | iex
```

### Méthode Manuelle

1. Clonez ce repo.
2. Rendez le script exécutable : `chmod +x review.py`
3. Créez un lien symbolique : `sudo ln -s $(pwd)/review.py /usr/local/bin/code-review`
4. Ajoutez votre `MISTRAL_API_KEY` dans un fichier `.env`.

### Désinstallation

```bash
# La méthode la plus simple
code-review --uninstall

# Ou via le one-liner si vous n'avez plus la commande
curl -sSL https://raw.githubusercontent.com/thefrcrazy/code-review/main/install.sh | bash -s -- --uninstall
```

## 🛠 Usage

Par défaut, le script crée la commande `code-review` (modifiable lors de l'installation).

```bash
# Analyse simple du dossier actuel
code-review .

# Analyse d'un dossier spécifique en français
code-review -l french /chemin/vers/projet

# Analyse détaillée (affiche tous les fichiers scannés)
code-review -v .

# Analyse avec une instruction spécifique
code-review . "Cherche uniquement des failles SQL et XSS"
```

## ⚙️ Configuration

### Le fichier `GUARD.md`
Placez un fichier `GUARD.md` à la racine de votre projet pour donner des instructions persistantes à l'IA. 
*Exemple : "Ce projet est en React/Node.js, sois très attentif à la gestion des hooks et aux permissions des API."*

### Variables d'environnement
- `MISTRAL_API_KEY` : **(Requis)** Votre clé API Mistral. Obtenez-en une ici : [console.mistral.ai/codestral](https://console.mistral.ai/codestral)
- `CODESTRAL_URL` : (Optionnel) Pour utiliser un endpoint différent (ex: proxy).

## 📁 Structure du Projet
```text
review_code/
├── review.py         # Le moteur principal (Python)
├── install.sh        # Script d'installation interactif
├── .env              # Configuration des clés
├── GUARD.md          # Instructions globales par défaut
└── reviews/          # Dossier de sortie des rapports (auto-généré au CWD)
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---
*Développé pour une revue de code rapide, efficace et visuelle.*
