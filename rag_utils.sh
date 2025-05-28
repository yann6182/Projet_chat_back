#!/bin/bash
# Script pour faciliter l'utilisation du système RAG

clear
echo "==========================================="
echo "Assistant juridique RAG avec Mistral AI"
echo "==========================================="

function menu {
    echo ""
    echo "Choisissez une option:"
    echo "1. Indexer des documents"
    echo "2. Tester le système RAG"
    echo "3. Démarrer le serveur API"
    echo "0. Quitter"
    echo ""

    read -p "Votre choix (0-3): " choix

    case $choix in
        1) indexer ;;
        2) tester ;;
        3) serveur ;;
        0) fin ;;
        *) menu ;;
    esac
}

function indexer {
    echo ""
    echo "== Indexation des documents =="
    read -p "Dossier des documents (par défaut: ./data): " dossier
    dossier=${dossier:-"./data"}
    read -p "Forcer la réindexation? (o/n, par défaut: n): " force

    if [[ "$force" == "o" || "$force" == "O" ]]; then
        python scripts/reindex.py --data "$dossier" --force
    else
        python scripts/reindex.py --data "$dossier"
    fi

    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    menu
}

function tester {
    echo ""
    echo "== Test du système RAG =="
    read -p "Votre question (ex: Quels sont les documents requis pour créer une association?): " query
    query=${query:-"Quels sont les documents requis pour créer une association?"}
    read -p "Mode de test (search/response/both, par défaut: both): " mode
    mode=${mode:-"both"}

    python scripts/test_rag.py --query "$query" --mode "$mode"

    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    menu
}

function serveur {
    echo ""
    echo "== Démarrage du serveur API =="
    echo "Appuyez sur Ctrl+C pour arrêter le serveur"
    python run.py
    menu
}

function fin {
    echo ""
    echo "Au revoir!"
    exit 0
}

# Démarrer le menu
menu
