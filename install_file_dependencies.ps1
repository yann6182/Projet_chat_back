# Script pour installer les dépendances nécessaires au traitement des fichiers
# Vérifiez les dépendances déjà installées et installez celles qui sont manquantes

$dependencies = @(
    "PyPDF2==3.0.1",
    "python-docx==1.1.0",
    "python-multipart==0.0.9",
    "docx2txt==0.8"
)

Write-Host "Installation des dépendances pour le traitement des fichiers..."

foreach ($dep in $dependencies) {
    Write-Host "Vérification de $dep"
    $package = $dep.Split("==")[0]
    pip show $package 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installation de $dep"
        pip install $dep
    } else {
        Write-Host "$package est déjà installé"
    }
}

Write-Host "Toutes les dépendances ont été installées avec succès!"
