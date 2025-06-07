import sys, os
import traceback
import requests
import json
import asyncio

# Fonction pour tester l'API de téléchargement et d'analyse de documents
async def test_file_analysis_api():
    print("Testing file analysis API...")
    
    # URL de base de l'API
    base_url = "http://localhost:8000/api/file-analysis"
    
    # Créer un document simple avec des erreurs pour le test
    test_content = """
    Ceci est un document de test pour une Junior-enterprize.
    Il contient des erreurs comme assemblee generale, et des termes 
    comme TVA sans avoir de numero de TVA. La signature electronique 
    est utilisee pour les contrats. Le president et le tresorier
    sont les principaux responsables financiers.
    """
    
    # Chemin du fichier temporaire
    temp_file_path = "data/test_document.txt"
    
    try:
        # Créer le fichier de test
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print(f"Created test file: {temp_file_path}")
        
        # 1. Authentification (simulée)
        auth_headers = {"Authorization": "Bearer test_token"}
        
        # 2. Télécharger le document
        with open(temp_file_path, "rb") as f:
            files = {"file": (os.path.basename(temp_file_path), f, "text/plain")}
            response = requests.post(f"{base_url}/upload", headers=auth_headers, files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            document_id = upload_result["document_id"]
            print(f"Document uploaded successfully. ID: {document_id}")
            
            # 3. Analyser le document
            analysis_payload = {"document_id": document_id}
            response = requests.post(f"{base_url}/analyze", headers=auth_headers, json=analysis_payload)
            
            if response.status_code == 200:
                analysis_result = response.json()
                print("\n--- Document Analysis Results ---")
                print(f"Spelling errors: {len(analysis_result['spelling_errors'])}")
                print(f"Grammar errors: {len(analysis_result['grammar_errors'])}")
                print(f"Legal issues: {len(analysis_result['legal_compliance_issues'])}")
                print(f"Compliance score: {analysis_result['overall_compliance_score']:.2f}")
                
                print("\nSuggestions:")
                for suggestion in analysis_result['suggestions']:
                    print(f" - {suggestion}")
                
                # 4. Poser une question sur le document
                query = "Quels sont les problèmes juridiques dans ce document?"
                query_payload = {
                    "query": query,
                    "document_id": document_id
                }
                response = requests.post(f"{base_url}/query", headers=auth_headers, data=query_payload)
                
                if response.status_code == 200:
                    query_result = response.json()
                    print("\n--- Document Query Results ---")
                    print(f"Query: {query}")
                    print(f"Answer: {query_result['answer']}")
                    
                    # Si des sources ont été fournies
                    if query_result.get('sources'):
                        print("\nSources:")
                        for source in query_result['sources']:
                            print(f" - {source}")
                else:
                    print(f"Error querying the document: {response.status_code}")
                    print(response.text)
            else:
                print(f"Error analyzing the document: {response.status_code}")
                print(response.text)
        else:
            print(f"Error uploading the document: {response.status_code}")
            print(response.text)
            
        return True
    
    except Exception as e:
        print(f"Error during API test: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Nettoyage: vérifier si le fichier existe avant de le supprimer
        if os.path.exists(temp_file_path):
            try:
                # os.unlink(temp_file_path)  # On garde le fichier pour référence
                print(f"Test file kept at: {temp_file_path}")
            except:
                pass

if __name__ == "__main__":
    # Exécuter le test de l'API de manière asynchrone
    asyncio.run(test_file_analysis_api())
