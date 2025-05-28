# PowerShell script d'utilisation de l'architecture RAG
param (
    [string]$Command = "help",
    [string]$DocsDir = "data\legal_docs"
)

# Couleurs pour le terminal
$RED = 'Red'
$GREEN = 'Green'
$YELLOW = 'Yellow'
$BLUE = 'Cyan'

# Fonction pour afficher un message stylisé
function Print-Message {
    param ([string]$Message)
    Write-Host "[RAG] " -ForegroundColor $BLUE -NoNewline
    Write-Host $Message
}

function Print-Success {
    param ([string]$Message)
    Write-Host "[✓] " -ForegroundColor $GREEN -NoNewline
    Write-Host $Message
}

function Print-Warning {
    param ([string]$Message)
    Write-Host "[!] " -ForegroundColor $YELLOW -NoNewline
    Write-Host $Message
}

function Print-Error {
    param ([string]$Message)
    Write-Host "[✗] " -ForegroundColor $RED -NoNewline
    Write-Host $Message
}

# Fonction pour installer les dépendances
function Install-Dependencies {
    Print-Message "Installation des dépendances RAG..."
    
    try {
        & pip install -r requirements-rag.txt
        Print-Success "Dépendances installées avec succès"
    }
    catch {
        Print-Error "Erreur lors de l'installation des dépendances: $_"
        exit 1
    }
}

# Fonction pour indexer les documents
function Index-Documents {
    param (
        [string]$DocsDirectory,
        [bool]$Force = $false
    )
    
    Print-Message "Indexation des documents dans $DocsDirectory..."
    
    if (-not (Test-Path $DocsDirectory)) {
        Print-Warning "Le répertoire $DocsDirectory n'existe pas. Création..."
        New-Item -Path $DocsDirectory -ItemType Directory | Out-Null
    }
    
    # Construire la commande
    $cmd = "python scripts\reindex_chromadb.py --docs-dir `"$DocsDirectory`""
    
    if ($Force) {
        $cmd += " --force-reindex"
        Print-Warning "Réindexation forcée (les données existantes seront effacées)"
    }
    
    # Exécuter la commande
    try {
        Invoke-Expression $cmd
        Print-Success "Indexation terminée avec succès"
    }
    catch {
        Print-Error "Erreur lors de l'indexation des documents: $_"
        exit 1
    }
}

# Fonction pour tester l'architecture RAG
function Test-RAG {
    Print-Message "Test de l'architecture RAG..."
    
    try {
        & python scripts\test_rag.py
        Print-Success "Test RAG terminé avec succès"
    }
    catch {
        Print-Error "Erreur lors du test RAG: $_"
        exit 1
    }
}

# Affichage de l'aide
function Show-Help {
    Write-Host "=== Utilitaire RAG pour le chatbot juridique ===" -ForegroundColor $BLUE
    Write-Host ""
    Write-Host "Usage: .\rag_utils.ps1 -Command <commande> [-DocsDir <répertoire>]"
    Write-Host ""
    Write-Host "Commandes disponibles:"
    Write-Host "  install          - Installe les dépendances nécessaires"
    Write-Host "  index            - Indexe les documents du répertoire spécifié"
    Write-Host "  reindex          - Réindexe en effaçant les données existantes"
    Write-Host "  test             - Teste l'architecture RAG"
    Write-Host "  help             - Affiche cette aide"
    Write-Host ""
    Write-Host "Exemples:"
    Write-Host "  .\rag_utils.ps1 -Command install                   # Installe les dépendances"
    Write-Host "  .\rag_utils.ps1 -Command index                     # Indexe les documents dans data\legal_docs"
    Write-Host "  .\rag_utils.ps1 -Command reindex -DocsDir docs\    # Réindexe les documents dans docs\"
    Write-Host "  .\rag_utils.ps1 -Command test                      # Teste l'architecture RAG"
}

# Traitement des commandes
switch ($Command.ToLower()) {
    "install" {
        Install-Dependencies
    }
    "index" {
        Index-Documents -DocsDirectory $DocsDir -Force $false
    }
    "reindex" {
        Index-Documents -DocsDirectory $DocsDir -Force $true
    }
    "test" {
        Test-RAG
    }
    "help" {
        Show-Help
    }
    default {
        Print-Error "Commande inconnue: $Command"
        Show-Help
        exit 1
    }
}
