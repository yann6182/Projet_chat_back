import sys, os
import traceback
sys.path.append(os.path.abspath('.'))
from app.services.document_generator_service import DocumentGeneratorService

# Test document generation with basic content
print('Starting test for document generator...')
doc_gen = DocumentGeneratorService()
try:
    print('Attempting to generate PDF...')
    pdf_path = doc_gen.generate_pdf(
        title='Test Document',
        content='This is a test content.\nMultiple lines of text.',
        metadata={'Author': 'Test User', 'Purpose': 'Testing'},
        sources=['Source 1', 'Source 2']
    )
    print(f'Successfully generated PDF: {pdf_path}')
except Exception as e:
    print(f'Error generating PDF: {str(e)}')
    traceback.print_exc()
