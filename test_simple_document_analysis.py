import sys, os
import traceback
sys.path.append(os.path.abspath('.'))
from app.services.document_service import DocumentService
import asyncio
import shutil

async def test_simple_document_analysis():
    print("Starting simple document analysis test...")
    
    # Create document service
    doc_service = DocumentService()
    
    # Create test content
    test_content = """
    Ceci est un document de test pour une Junior-enterprize.
    Il contient des erreurs comme assemblee generale, et des termes 
    comme TVA sans avoir de numero de TVA. La signature electronique 
    est utilisee pour les contrats. Le president et le tresorier
    sont les principaux responsables financiers.
    """
    
    # Create test document
    test_file_path = "data/test_document.txt"
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file_path}")
    
    # Save the document
    document_id = None
    try:
        # Read the file in binary mode
        with open(test_file_path, "rb") as f:
            document_id = await doc_service.save_document(f, "test_document.txt")
        
        print(f"Document saved with ID: {document_id}")
        
        # Analyze the document
        if document_id:
            analysis = await doc_service.analyze_document(document_id)
            
            print("\n--- Document Analysis Results ---")
            print(f"Document ID: {analysis.document_id}")
            print(f"Filename: {analysis.filename}")
            
            print(f"\nSpelling errors: {len(analysis.spelling_errors)}")
            for i, error in enumerate(analysis.spelling_errors):
                print(f"  {i+1}. '{error.word}' (suggestions: {', '.join(error.suggestions)})")
            
            print(f"\nGrammar errors: {len(analysis.grammar_errors)}")
            for i, error in enumerate(analysis.grammar_errors):
                print(f"  {i+1}. '{error.text}' - {error.message}")
                if error.suggestions:
                    print(f"     Suggestions: {', '.join(error.suggestions)}")
            
            print(f"\nLegal issues: {len(analysis.legal_compliance_issues)}")
            for i, issue in enumerate(analysis.legal_compliance_issues):
                print(f"  {i+1}. {issue.issue_type}: {issue.description}")
                print(f"     Recommendation: {issue.recommendation}")
            
            print(f"\nCompliance score: {analysis.overall_compliance_score:.2f}")
            
            print("\nSuggestions:")
            for i, suggestion in enumerate(analysis.suggestions):
                print(f"  {i+1}. {suggestion}")
                
            return {
                "document_id": document_id,
                "analysis": analysis
            }
    except Exception as e:
        print(f"Error during test: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_simple_document_analysis())
