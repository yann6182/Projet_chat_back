from typing import Dict, List, BinaryIO, Optional
import os
import uuid
import docx2txt
import PyPDF2
import spacy
from pptx import Presentation
from app.schemas.document import DocumentAnalysisResponse, SpellingError, GrammarError, LegalComplianceIssue

class DocumentService:
    def __init__(self):
        self.nlp = spacy.load("fr_core_news_md")
        self.upload_dir = "data/user_uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        
        self.legal_terms = [
            "junior entreprise", "statut associatif", "CNJE", "étudiant entrepreneur",
            "prestation intellectuelle", "convention", "facturation", "TVA",
            "responsabilité civile professionnelle", "cotisation", "assemblée générale"
        ]
    
        
    async def save_document(self, file: BinaryIO, filename: str) -> str:
        """
        Sauvegarde un document téléchargé et retourne son identifiant unique.
        
        Args:
            file: Le fichier téléchargé
            filename: Le nom du fichier
            
        Returns:
            L'identifiant unique du document
        """
        document_id = str(uuid.uuid4())
        
        _, ext = os.path.splitext(filename)
        
        file_path = os.path.join(self.upload_dir, f"{document_id}{ext}")
        
        with open(file_path, "wb") as f:
            f.write(file.read())
            
        return document_id
        
    async def analyze_document(self, document_id: str) -> DocumentAnalysisResponse:
        """
        Analyse un document pour vérifier son orthographe, sa grammaire et sa conformité légale.
        
        Args:
            document_id: L'identifiant du document à analyser
            
        Returns:
            Le résultat de l'analyse du document
        """
        file_path, filename = self.find_document_by_id(document_id)
        
        if not file_path:
            raise FileNotFoundError(f"Document avec l'ID {document_id} non trouvé")
            
        text = self.extract_text(file_path)
        
        spelling_errors = self.check_spelling(text)
        grammar_errors = self.check_grammar(text)
        legal_compliance_issues = self.check_legal_compliance(text)
        
        total_issues = len(spelling_errors) + len(grammar_errors) + len(legal_compliance_issues)
        compliance_score = max(0.0, 1.0 - (total_issues / 100)) if total_issues > 0 else 1.0
        
        suggestions = self.generate_suggestions(text, spelling_errors, grammar_errors, legal_compliance_issues)
        
        return DocumentAnalysisResponse(
            document_id=document_id,
            filename=filename,
            spelling_errors=spelling_errors,
            grammar_errors=grammar_errors,
            legal_compliance_issues=legal_compliance_issues,
            overall_compliance_score=compliance_score,
            suggestions=suggestions
        )
        
    def find_document_by_id(self, document_id: str) -> tuple:
        """
        Recherche un document par son identifiant.
        
        Args:
            document_id: L'identifiant du document
            
        Returns:
            Un tuple contenant le chemin du fichier et son nom
        """
        for filename in os.listdir(self.upload_dir):
            if filename.startswith(document_id):
                return os.path.join(self.upload_dir, filename), filename
        return None, None
        
    def extract_text(self, file_path: str) -> str:
        """
        Extrait le texte d'un document selon son format.
        
        Args:
            file_path: Le chemin du fichier
            
        Returns:
            Le texte extrait du document
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        elif ext in [".pptx", ".ppt"]:
            return self.extract_text_from_pptx(file_path)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"Format de fichier non pris en charge: {ext}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier PDF.
        
        Args:
            file_path: Le chemin du fichier PDF
            
        Returns:
            Le texte extrait du PDF
        """
        text = ""
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
        
    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier DOCX.
        
        Args:
            file_path: Le chemin du fichier DOCX
            
        Returns:
            Le texte extrait du DOCX
        """
        return docx2txt.process(file_path)
        
    def extract_text_from_pptx(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier PowerPoint.
        
        Args:
            file_path: Le chemin du fichier PowerPoint
            
        Returns:
            Le texte extrait du PowerPoint
        """
        text = ""
        prs = Presentation(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
        
    def check_spelling(self, text: str) -> List[SpellingError]:
        """
        Vérifie l'orthographe du texte.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste d'erreurs d'orthographe
        """
        doc = self.nlp(text)
        errors = []
        
       
        for token in doc:
            if token.is_alpha and not token.is_stop and len(token.text) > 3:
                # Simuler une erreur pour certains mots (à remplacer par une véritable vérification)
                if len(token.text) > 10 and token.text not in self.nlp.vocab:
                    errors.append(
                        SpellingError(
                            word=token.text,
                            position={"start": token.idx, "end": token.idx + len(token.text)},
                            suggestions=[f"{token.text[:-1]}", f"{token.text}e", f"{token.text}s"]
                        )
                    )
        
        return errors
        
    def check_grammar(self, text: str) -> List[GrammarError]:
        """
        Vérifie la grammaire du texte.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste d'erreurs grammaticales
        """
        doc = self.nlp(text)
        errors = []
        
        for i, token in enumerate(doc):
            if token.is_alpha and i > 0:
                # Vérifier les accords simples (exemple simplifié)
                if token.pos_ == "NOUN" and doc[i-1].pos_ == "ADJ":
                    if token.morph.get("Gender") != doc[i-1].morph.get("Gender"):
                        errors.append(
                            GrammarError(
                                text=f"{doc[i-1].text} {token.text}",
                                position={"start": doc[i-1].idx, "end": token.idx + len(token.text)},
                                message="Possible problème d'accord en genre",
                                suggestions=[f"{doc[i-1].text}e {token.text}"]
                            )
                        )
        
        return errors
        
    def check_legal_compliance(self, text: str) -> List[LegalComplianceIssue]:
        """
        Vérifie la conformité légale du texte.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste de problèmes de conformité légale
        """
        doc = self.nlp(text.lower())
        issues = []
        
        missing_terms = []
        for term in self.legal_terms:
            if term not in text.lower():
                missing_terms.append(term)
        
        if missing_terms:
            issues.append(
                LegalComplianceIssue(
                    text="",
                    position={"start": 0, "end": 0},
                    issue_type="Termes manquants",
                    description=f"Les termes juridiques suivants sont absents du document : {', '.join(missing_terms)}",
                    recommendation="Considérez ajouter ces termes pour améliorer la conformité juridique."
                )
            )
        
        if "TVA" in text and "numéro de TVA" not in text.lower():
            issues.append(
                LegalComplianceIssue(
                    text="TVA",
                    position={"start": text.lower().find("tva"), "end": text.lower().find("tva") + 3},
                    issue_type="Mention légale incomplète",
                    description="La TVA est mentionnée mais le numéro de TVA n'est pas précisé.",
                    recommendation="Ajoutez le numéro de TVA intracommunautaire."
                )
            )
        
        return issues
        
    def generate_suggestions(self, text: str, spelling_errors: List[SpellingError], 
                            grammar_errors: List[GrammarError], 
                            legal_issues: List[LegalComplianceIssue]) -> List[str]:
        """
        Génère des suggestions d'amélioration basées sur les erreurs détectées.
        
        Args:
            text: Le texte analysé
            spelling_errors: Les erreurs d'orthographe détectées
            grammar_errors: Les erreurs grammaticales détectées
            legal_issues: Les problèmes de conformité légale détectés
            
        Returns:
            Une liste de suggestions d'amélioration
        """
        suggestions = []
        
        if spelling_errors:
            suggestions.append(f"Corrigez les {len(spelling_errors)} erreurs d'orthographe identifiées.")
        
        if grammar_errors:
            suggestions.append(f"Corrigez les {len(grammar_errors)} erreurs grammaticales identifiées.")
        
        for issue in legal_issues:
            suggestions.append(issue.recommendation)
        
        if "junior entreprise" not in text.lower():
            suggestions.append("Mentionnez explicitement 'Junior Entreprise' dans votre document.")
        
        if "CNJE" not in text:
            suggestions.append("Considérez mentionner la CNJE (Confédération Nationale des Junior-Entreprises).")
        
        return suggestions
def process_document(content: bytes, filename: str) -> dict:
    """
    Traite un document et retourne les résultats de l'analyse.
    
    Args:
        content: Le contenu du fichier en bytes.
        filename: Le nom du fichier.
    
    Returns:
        Un dictionnaire contenant les résultats de l'analyse.
    """
    return {"filename": filename, "status": "processed"}
