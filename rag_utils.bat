@echo off
REM Script pour faciliter l'utilisation du système RAG

echo ===========================================
echo Assistant juridique RAG avec Mistral AI
echo ===========================================

:menu
echo.
echo Choisissez une option:
echo 1. Indexer des documents
echo 2. Tester le système RAG
echo 3. Démarrer le serveur API
echo 0. Quitter
echo.

set /p choix="Votre choix (0-3): "

if "%choix%"=="1" goto indexer
if "%choix%"=="2" goto tester
if "%choix%"=="3" goto serveur
if "%choix%"=="0" goto fin
goto menu

:indexer
echo.
echo == Indexation des documents ==
set /p dossier="Dossier des documents (par défaut: ./data): "
if "%dossier%"=="" set dossier=./data
set /p force="Forcer la réindexation? (o/n, par défaut: n): "

if /i "%force%"=="o" (
    python scripts/reindex.py --data %dossier% --force
) else (
    python scripts/reindex.py --data %dossier%
)

echo.
pause
goto menu

:tester
echo.
echo == Test du système RAG ==
set /p query="Votre question (ex: Quels sont les documents requis pour créer une association?): "
if "%query%"=="" set query="Quels sont les documents requis pour créer une association?"
set /p mode="Mode de test (search/response/both, par défaut: both): "
if "%mode%"=="" set mode=both

python scripts/test_rag.py --query "%query%" --mode %mode%

echo.
pause
goto menu

:serveur
echo.
echo == Démarrage du serveur API ==
echo Appuyez sur Ctrl+C pour arrêter le serveur
python run.py
goto menu

:fin
echo.
echo Au revoir!
exit
