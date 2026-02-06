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
CYAN='\033[0;36m'
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
    
    echo -ne "Nom de la commande à supprimer [code-review] : "
    read BIN_NAME < /dev/tty
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
    
    echo -ne "Êtes-vous sûr ? (y/N) "
    read confirm < /dev/tty
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
    echo -e "\n${YELLOW}${BOLD}󰄵 Étape 1 :${NC} ${BOLD}Emplacement des fichiers${NC}"
    echo -ne "${BLUE}➜${NC} Où voulez-vous installer le script ? [${CYAN}$DEFAULT_DIR${NC}] : "
    read INSTALL_DIR < /dev/tty
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}
    
    # 2. Choix du nom de la commande
    DEFAULT_NAME="code-review"
    echo -e "\n${YELLOW}${BOLD}󰄵 Étape 2 :${NC} ${BOLD}Nom du raccourci${NC}"
    echo -ne "${BLUE}➜${NC} Quel nom de commande voulez-vous utiliser ? [${CYAN}$DEFAULT_NAME${NC}] : "
    read BIN_NAME < /dev/tty
    BIN_NAME=${BIN_NAME:-$DEFAULT_NAME}
    
    echo -e "\n${BLUE}📦${NC} Préparation de l'installation dans ${CYAN}$INSTALL_DIR${NC}..."
    mkdir -p "$INSTALL_DIR"
    
    # 3. Téléchargement
    echo -e "${BLUE}📥${NC} Téléchargement depuis GitHub..."
    if [ -f "review.py" ]; then
        cp "review.py" "$INSTALL_DIR/review.py"
        cp "install.sh" "$INSTALL_DIR/install.sh"
    else
        curl -sSL "$RAW_URL" -o "$INSTALL_DIR/review.py"
        curl -sSL "https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/install.sh" -o "$INSTALL_DIR/install.sh"
    fi
    
    chmod +x "$INSTALL_DIR/review.py"
    chmod +x "$INSTALL_DIR/install.sh"
    
    # 4. Lien symbolique
    echo -e "${BLUE}🔗${NC} Création du raccourci ${CYAN}'$BIN_NAME'${NC} dans ${BOLD}/usr/local/bin${NC} (nécessite sudo)..."
    if [ -L "/usr/local/bin/$BIN_NAME" ]; then
        sudo rm "/usr/local/bin/$BIN_NAME"
    fi
    sudo ln -s "$INSTALL_DIR/review.py" "/usr/local/bin/$BIN_NAME"
    
    # 5. Configuration API
    ENV_FILE="$INSTALL_DIR/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "\n${YELLOW}${BOLD}󰄵 Étape 3 :${NC} ${BOLD}Configuration API (Mistral)${NC}"
        echo -e "${BLUE}ℹ${NC} Obtenez une clé gratuite ici : ${CYAN}${BOLD}https://console.mistral.ai/codestral${NC}"
        
        if [ -n "$MISTRAL_API_KEY" ]; then
            echo -e "${GREEN}✔${NC} MISTRAL_API_KEY détectée dans votre environnement."
            echo "MISTRAL_API_KEY=$MISTRAL_API_KEY" > "$ENV_FILE"
        else
            echo -ne "${BLUE}➜${NC} Entrez votre clé ${BOLD}MISTRAL_API_KEY${NC} (laisser vide pour plus tard) : "
            read USER_KEY < /dev/tty
            if [ -n "$USER_KEY" ]; then
                echo "MISTRAL_API_KEY=$USER_KEY" > "$ENV_FILE"
                echo -e "${GREEN}✔${NC} Clé sauvegardée avec succès."
            else
                echo -e "${YELLOW}⚠️${NC}  N'oubliez pas de configurer votre clé plus tard dans : ${BOLD}$ENV_FILE${NC}"
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