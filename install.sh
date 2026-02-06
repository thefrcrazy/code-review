#!/bin/bash

# Configuration
REPO_USER="thefrcrazy"
REPO_NAME="code-review"
BRANCH="main"
RAW_URL="https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/review.py"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

function print_banner() {
    echo -e "${BLUE}${BOLD}"
    echo "   ______      __         ____                 _                 "
    echo "  / ____/___  / /__      / __ \___ _   _(_)__ _      __          "
    echo " / /   / __ \/ / _ \    / /_/ / _ \ | / / / _ \ | /| / /         "
    echo "/ /___/ /_/ / /  __/   / _, _/  __/ |/ / /  __/ |/ |/ /          "
    echo "\____/\____/_/\___/   /_/ |_|\___/|___/_/\___/|__/|__/           "
    echo "                                                                  "
    echo -e "              Code Review CLI Installer${NC}"
    echo ""
}

function uninstall() {
    echo -e "${RED}${BOLD}🗑️  Désinstallation de Code Review${NC}"
    
    read -p "Nom de la commande à supprimer [code-review] : " BIN_NAME
    BIN_NAME=${BIN_NAME:-code-review}
    
    BIN_PATH=$(which $BIN_NAME 2>/dev/null)
    
    if [ -z "$BIN_PATH" ]; then
        echo -e "${RED}❌ Commande '$BIN_NAME' introuvable.${NC}"
        exit 1
    fi
    
    # Trouver le vrai dossier via le lien symbolique
    REAL_SCRIPT=$(readlink -f "$BIN_PATH")
    INSTALL_DIR=$(dirname "$REAL_SCRIPT")
    
    echo -e "📍 Installation détectée dans : $INSTALL_DIR"
    echo -e "⚠️  Cela va supprimer :"
    echo -e "   - Le lien : $BIN_PATH"
    echo -e "   - Le dossier : $INSTALL_DIR"
    
    read -p "Êtes-vous sûr ? (y/N) " confirm
    if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
        echo "Annulation."
        exit 0
    fi
    
    echo "Suppression du lien symbolique..."
    sudo rm "$BIN_PATH"
    
    echo "Suppression du dossier..."
    rm -rf "$INSTALL_DIR"
    
    echo -e "${GREEN}✔ Désinstallation terminée avec succès.${NC}"
    exit 0
}

function install() {
    echo -e "${BLUE}${BOLD}🚀 Installation de Code Review${NC}"
    
    # 1. Choix du dossier d'installation
    DEFAULT_DIR="$HOME/.code-review"
    read -p "Dossier d'installation [$DEFAULT_DIR] : " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}
    
    # 2. Choix du nom de la commande
    DEFAULT_NAME="code-review"
    read -p "Nom du raccourci commande [$DEFAULT_NAME] : " BIN_NAME
    BIN_NAME=${BIN_NAME:-$DEFAULT_NAME}
    
    echo -e "\n📦 Préparation..."
    mkdir -p "$INSTALL_DIR"
    
    # 3. Téléchargement
    echo -e "📥 Téléchargement depuis GitHub..."
    # Note: On utilise curl pour télécharger. Si le repo n'est pas encore public/existant, cela échouera.
    # Pour le test local, on copie si le fichier existe, sinon on tente le curl
    if [ -f "review.py" ]; then
        cp "review.py" "$INSTALL_DIR/review.py"
    else
        HTTP_CODE=$(curl -sSL -w "%{http_code}" "$RAW_URL" -o "$INSTALL_DIR/review.py")
        if [ "$HTTP_CODE" -ne 200 ]; then
            echo -e "${RED}❌ Erreur de téléchargement (HTTP $HTTP_CODE). Vérifiez l'URL du repo.${NC}"
            echo -e "URL tentée : $RAW_URL"
            exit 1
        fi
    fi
    
    chmod +x "$INSTALL_DIR/review.py"
    
    # 4. Lien symbolique
    echo -e "🔗 Création du raccourci '${BIN_NAME}' (nécessite sudo)..."
    if [ -L "/usr/local/bin/$BIN_NAME" ]; then
        sudo rm "/usr/local/bin/$BIN_NAME"
    fi
    sudo ln -s "$INSTALL_DIR/review.py" "/usr/local/bin/$BIN_NAME"
    
    # 5. Configuration API
    ENV_FILE="$INSTALL_DIR/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "\n${YELLOW}🔑 Configuration API (Mistral)${NC}"
        echo -e "Obtenez une clé gratuite ici : ${BOLD}https://console.mistral.ai/codestral${NC}"
        if [ -n "$MISTRAL_API_KEY" ]; then
            echo "MISTRAL_API_KEY détectée dans l'environnement."
            echo "MISTRAL_API_KEY=$MISTRAL_API_KEY" > "$ENV_FILE"
        else
            read -p "Entrez votre clé MISTRAL_API_KEY (laisser vide pour configurer plus tard) : " USER_KEY
            if [ -n "$USER_KEY" ]; then
                echo "MISTRAL_API_KEY=$USER_KEY" > "$ENV_FILE"
                echo -e "${GREEN}✔ Clé sauvegardée.${NC}"
            else
                echo "⚠️  N'oubliez pas de configurer votre clé plus tard."
            fi
        fi
    else
        echo -e "📄 Fichier .env existant conservé."
    fi
    
    echo -e "\n${GREEN}${BOLD}✨ Installation terminée !${NC}"
    echo -e "Essayez maintenant : ${BLUE}$BIN_NAME .${NC}"
}

# --- Main ---

print_banner

if [[ "$1" == "--uninstall" ]]; then
    uninstall
else
    install
fi