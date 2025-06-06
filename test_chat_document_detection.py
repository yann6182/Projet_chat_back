import sys, os
import traceback
sys.path.append(os.path.abspath('.'))
from app.services.document_generator_service import DocumentGeneratorService
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest

async def test_document_detection_and_generation():
    print("Starting comprehensive test for document detection and generation...")
    
    # Initialize chat service
    chat_service = ChatService()
    
    try:
        # Test with a query that explicitly requests a PDF document
        conversation_id = "test_conversation_123"
        user_id = 1
        query = "Quelles sont les obligations fiscales d'une Junior-Entreprise? Donne-moi un document PDF avec ta réponse."
        
        print(f"Sending query: {query}")
        request = ChatRequest(query=query)
        
        # Process the query
        print("Processing query through the chat service...")
        response = await chat_service.process_query(request, conversation_id, user_id)
        
        # Check if a document was generated
        if response.generated_document:
            print(f"Success! Document was generated:")
            print(f"Format: {response.generated_document.format}")
            print(f"Filename: {response.generated_document.filename}")
            print(f"URL: {response.generated_document.url}")
        else:
            print("No document was generated. Check the document detection logic.")
        
        return response
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import asyncio
    response = asyncio.run(test_document_detection_and_generation())
