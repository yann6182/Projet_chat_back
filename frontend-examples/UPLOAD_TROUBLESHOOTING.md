# Guide de résolution des erreurs d'upload (422 Unprocessable Entity)

Si vous rencontrez des erreurs 422 (Unprocessable Entity) lors de l'upload de documents vers l'API, ce guide vous aidera à résoudre les problèmes les plus courants.

## Contexte

L'erreur 422 signifie généralement que votre requête a été comprise par le serveur, mais qu'elle contient des données invalides ou que le format de la requête n'est pas correct.

## Problèmes courants et solutions

### 1. Erreur concernant le format du fichier

**Symptôme**: Vous recevez une erreur 422 avec un message comme "Format de fichier non pris en charge".

**Solution**: Assurez-vous que le fichier que vous essayez d'uploader a l'une des extensions suivantes:
- .pdf
- .txt
- .docx
- .doc

### 2. Erreur dans le format FormData

**Symptôme**: L'API renvoie une erreur 422 sans message d'erreur spécifique.

**Solution**: Les données doivent être envoyées dans le bon format FormData. Le nom du champ pour le fichier doit être exactement "file".

```javascript
// Correct
const formData = new FormData();
formData.append('file', file); // IMPORTANT: Le nom doit être exactement "file"
```

### 3. En-têtes Content-Type incorrects

**Symptôme**: L'API ne reconnaît pas le format multipart/form-data.

**Solution**: Ne définissez pas manuellement le Content-Type dans les en-têtes de la requête. Axios le fera automatiquement pour les objets FormData.

```javascript
// INCORRECT
const response = await axios.post(url, formData, {
  headers: {
    'Content-Type': 'multipart/form-data' // NE PAS DÉFINIR!
  }
});

// CORRECT
const response = await axios.post(url, formData, {
  headers: {
    'Authorization': `Bearer ${token}`
    // Axios ajoutera automatiquement le Content-Type avec la boundary
  }
});
```

### 4. Structure du FormData incorrecte

**Symptôme**: Les données sont envoyées mais l'API renvoie une erreur 422.

**Solution**: Vérifiez que le FormData est construit correctement et que chaque champ est ajouté indépendamment :

```javascript
// Construction correcte du FormData
const formData = new FormData();
formData.append('file', file);
formData.append('description', description);

// Débogage du contenu du FormData
for (let pair of formData.entries()) {
  console.log(pair[0] + ': ' + pair[1]);
}
```

## Vérification côté Backend

Le backend attend un fichier envoyé via un champ nommé "file" et un champ optionnel "description".

Dans le code backend, la structure attendue est :

```python
@router.post("/upload-source", response_model=DocumentResponse)
async def upload_source_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
```

## Tests avec Postman ou curl

Si vous rencontrez toujours des problèmes, vous pouvez tester l'API directement avec Postman ou curl :

### Avec curl

```bash
# Obtenir un token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -d "username=admin@example.com&password=your_password" \
  | jq -r '.access_token')

# Upload d'un fichier
curl -X POST http://localhost:8000/api/admin/upload-source \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/chemin/vers/votre/fichier.txt" \
  -F "description=Description du fichier"
```

Cette approche vous permettra de confirmer si le problème vient de votre application frontend ou de l'API elle-même.
