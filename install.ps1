param (
    [switch]$Uninstall
)

$RepoUser = "thefrcrazy"
$RepoName = "code-review"
$Branch = "main"
$RawUrl = "https://raw.githubusercontent.com/$RepoUser/$RepoName/$Branch/review.py"
$InstallUrl = "https://raw.githubusercontent.com/$RepoUser/$RepoName/$Branch/install.ps1"

function Print-Banner {
    Write-Host @"
   ______      __         ____                 _                 
  / ____/___  / /__      / __ \___ _   _(_)__ _      __          
 / /   / __ \/ / _ \    / /_/ / _ \ | / / / _ \ | /| / /         
/ /___/ /_/ / /  __/   / _, _/  __/ |/ / /  __/ |/ |/ /          
\____/\____/_/\___/   /_/ |_|\___/|___/_/\___/|__/|__/           

              Code Review CLI Installer (Windows)
"@ -ForegroundColor Cyan
}

if ($Uninstall) {
    Write-Host "`n🗑️  Désinstallation de Code Review..." -ForegroundColor Red
    $BinName = Read-Host "Nom de la commande à supprimer [code-review]"
    if (-not $BinName) { $BinName = "code-review" }

    $CommandPath = Get-Command $BinName -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $CommandPath) {
        Write-Host "❌ Commande '$BinName' introuvable." -ForegroundColor Red
        exit
    }

    $InstallDir = Split-Path (Get-Item $CommandPath).Target
    Write-Host "📍 Installation détectée dans : $InstallDir"
    
    $confirm = Read-Host "Êtes-vous sûr de vouloir tout supprimer ? (y/N)"
    if ($confirm -ne "y") { Write-Host "Annulé."; exit }

    Remove-Item $CommandPath -Force
    Remove-Item $InstallDir -Recurse -Force
    Write-Host "✔ Désinstallation terminée." -ForegroundColor Green
    exit
}

Print-Banner

# 1. Dossier d'installation
$DefaultDir = Join-Path $HOME ".code-review"
Write-Host "`n󰄵 Étape 1 : Emplacement des fichiers" -ForegroundColor Yellow
$InstallDir = Read-Host "Où voulez-vous installer le script ? [$DefaultDir]"
if (-not $InstallDir) { $InstallDir = $DefaultDir }

# 2. Nom de la commande
$DefaultName = "code-review"
Write-Host "`n󰄵 Étape 2 : Nom du raccourci" -ForegroundColor Yellow
$BinName = Read-Host "Quel nom de commande voulez-vous utiliser ? [$DefaultName]"
if (-not $BinName) { $BinName = $DefaultName }

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# 3. Téléchargement
Write-Host "📥 Téléchargement depuis GitHub..." -ForegroundColor Blue
if (Test-Path "review.py") {
    Copy-Item "review.py" (Join-Path $InstallDir "review.py")
    Copy-Item "install.ps1" (Join-Path $InstallDir "install.ps1")
} else {
    Invoke-WebRequest -Uri $RawUrl -OutFile (Join-Path $InstallDir "review.py")
    Invoke-WebRequest -Uri $InstallUrl -OutFile (Join-Path $InstallDir "install.ps1")
}

# 4. Création du "raccourci" (App Execution Alias via un petit bat)
$BinPath = Join-Path $InstallDir "$BinName.bat"
"@echo off`npython `"$InstallDireview.py`" %*" | Out-File $BinPath -Encoding ascii

# Ajout au PATH de l'utilisateur si nécessaire
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    Write-Host "🔗 Ajout au PATH de l'utilisateur..." -ForegroundColor Blue
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path += ";$InstallDir"
}

# 5. Clé API
$EnvFile = Join-Path $InstallDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "`n󰄵 Étape 3 : Configuration API (Mistral)" -ForegroundColor Yellow
    Write-Host "Obtenez une clé ici : https://console.mistral.ai/codestral"
    Write-Host "Entrez votre clé MISTRAL_API_KEY (saisie masquée) : " -NoNewline
    $SecureKey = Read-Host -AsSecureString
    $UserKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureKey))
    
    if ($UserKey) {
        "MISTRAL_API_KEY=$UserKey" | Out-File $EnvFile -Encoding utf8
        Write-Host "`n✔ Clé sauvegardée." -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  N'oubliez pas de configurer votre clé plus tard." -ForegroundColor Yellow
    }
}

Write-Host "`n✨ Installation terminée !" -ForegroundColor Green
Write-Host "Redémarrez votre terminal et essayez : $BinName ." -ForegroundColor Blue
