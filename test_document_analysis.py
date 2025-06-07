import sys, os
import traceback
sys.path.append(os.path.abspath('.'))
from fastapi import UploadFile
import asyncio
import tempfile

from app.services.document_service import DocumentService

async def test_document_analysis():
    print("Starting document analysis and correction test...")
    
    # Initialize document service
    doc_service = DocumentService()
    
    try:
        # Créer un document simple avec des erreurs pour le test
        test_content = """
        Ceci est un document de test pour une Junior-enterprize.
        Il contient des erreurs comme assemblee generale, et des termes 
        comme TVA sans avoir de numero de TVA. La signature electronique 
        est utilisee pour les contrats. Le president et le tresorier
        sont les principaux responsables financiers.
        """
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            print(f"Created test file: {temp_file_path}")
            
            # Ouvrir le fichier en mode binaire pour simuler un téléchargement
            with open(temp_file_path, "rb") as f:
                # Simuler un téléchargement de fichier
                document_id = await doc_service.save_document(f, os.path.basename(temp_file_path))
                
                print(f"Document saved with ID: {document_id}")
                
                # Analyser le document
                analysis = await doc_service.analyze_document(document_id)
                
                print("\n--- Analyse du document ---")
                print(f"Erreurs d'orthographe: {len(analysis.spelling_errors)}")
                for error in analysis.spelling_errors:
                    print(f" - {error.word} (suggestions: {', '.join(error.suggestions)})")
                
                print(f"\nErreurs grammaticales: {len(analysis.grammar_errors)}")
                for error in analysis.grammar_errors:
                    print(f" - {error.text} (message: {error.message})")
                
                print(f"\nProblèmes juridiques: {len(analysis.legal_compliance_issues)}")
                for issue in analysis.legal_compliance_issues:
                    print(f" - {issue.issue_type}: {issue.description}")
                    print(f"   Recommandation: {issue.recommendation}")
                
                print(f"\nScore global: {analysis.overall_compliance_score:.2f}")
                
                print("\nSuggestions:")
                for suggestion in analysis.suggestions:
                    print(f" - {suggestion}")
                
                # Test de correction automatique
                # Note: cette fonction n'est pas encore implémentée, nous simulons son comportement
                print("\n--- Simulation de correction automatique ---")
                corrections = {
                    "Junior-enterprize": "Junior-entreprise",
                    "assemblee generale": "assemblée générale",
                    "numero de TVA": "numéro de TVA",
                    "signature electronique": "signature électronique",
                    "president": "président",
                    "tresorier": "trésorier"
                }
                
                corrected_text = test_content
                for original, corrected in corrections.items():
                    corrected_text = corrected_text.replace(original, corrected)
                
                print("Texte corrigé:")
                print(corrected_text)
                
                return {
                    "document_id": document_id,
                    "analysis": analysis,
                    "file_path": temp_file_path
                }
        finally:
            # Nettoyage: supprimer le fichier temporaire
            try:
                os.unlink(temp_file_path)
                print(f"Removed temporary file: {temp_file_path}")
            except:
                pass
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_document_analysis())
