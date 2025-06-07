# app/services/document_service.py
from typing import Dict, List, BinaryIO, Optional
import os
import uuid
import docx2txt
import PyPDF2
import spacy
from pptx import Presentation
import language_tool_python
from spellchecker import SpellChecker
import re
from app.schemas.document import DocumentAnalysisResponse, SpellingError, GrammarError, LegalComplianceIssue
from app.services.chat_service import ChatService

class DocumentService:
    def __init__(self):
        # Charger le modèle spaCy pour l'analyse linguistique en français
        try:
            self.nlp = spacy.load("fr_core_news_md")
        except IOError:
            # Fallback vers le modèle plus petit si le grand n'est pas disponible
            self.nlp = spacy.load("fr_core_news_sm")
        
        self.upload_dir = "data/user_uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Initialiser les outils de vérification avancée
        self.grammar_tool = language_tool_python.LanguageTool('fr')
        self.spell_checker = SpellChecker(language='fr')
        
        # Initialiser le service de chat pour les analyses juridiques
        self.chat_service = ChatService()
        
        # Liste de termes juridiques spécifiques aux Juniors Entreprises
        self.legal_terms = [
            "junior entreprise", "statut associatif", "CNJE", "étudiant entrepreneur",
            "prestation intellectuelle", "convention", "facturation", "TVA",
            "responsabilité civile professionnelle", "cotisation", "assemblée générale",
            "contrat de prestation", "devis", "facture", "TVA intracommunautaire",
            "responsabilité civile", "assurance", "statuts", "règlement intérieur",
            "conseil d'administration", "assemblée générale ordinaire", "AGO",
            "assemblée générale extraordinaire", "AGE", "bilan financier",
            "compte de résultat", "trésorier", "président", "vice-président",
            "secrétaire général", "commissaire aux comptes", "auditeur",
            "junior-entreprise", "JE", "étudiant", "école", "université",
            "formation", "compétences", "mission", "client", "prospect",
            "commercial", "développement", "qualité", "suivi", "livrable"
        ]
        
        # Expressions juridiques importantes à vérifier
        self.legal_expressions = [
            r"numéro de TVA",
            r"TVA intracommunautaire",
            r"responsabilité civile professionnelle",
            r"assurance responsabilité civile",
            r"numéro SIRET",
            r"code APE",
            r"conditions générales",
            r"clause de confidentialité",
            r"propriété intellectuelle",
            r"droit d'auteur",
            r"délai de paiement",
            r"pénalités de retard",
            r"tribunal compétent",
            r"droit applicable"
        ]
        
        # Dictionnaire de corrections courantes pour l'orthographe française
        self.common_corrections = {
            "contract": "contrat",
            "signature electronique": "signature électronique",
            "assemblee": "assemblée",
            "president": "président",
            "tresorier": "trésorier",
            "prestation": "prestation",
            "junior-enterprise": "junior-entreprise",
            "cnje": "CNJE",
            "developper": "développer",
            "etudiant": "étudiant",
            "universite": "université",
            "ecole": "école"
        }
    
        
    async def save_document(self, file: BinaryIO, filename: str) -> str:
        """
        Sauvegarde un document téléchargé et retourne son identifiant unique.
        
        Args:
            file: Le fichier téléchargé
            filename: Le nom du fichier
            
        Returns:
            L'identifiant unique du document
        """
        # Générer un ID unique pour le document
        document_id = str(uuid.uuid4())
        
        # Déterminer l'extension du fichier
        _, ext = os.path.splitext(filename)
        
        # Créer le chemin complet
        file_path = os.path.join(self.upload_dir, f"{document_id}{ext}")
        
        # Sauvegarder le fichier
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
        # Trouver le fichier correspondant à l'ID
        file_path, filename = self.find_document_by_id(document_id)
        
        if not file_path:
            raise FileNotFoundError(f"Document avec l'ID {document_id} non trouvé")
            
        # Extraire le texte du document
        text = self.extract_text(file_path)
          # Analyser le texte
        spelling_errors = self.check_spelling(text)
        grammar_errors = self.check_grammar(text)
        legal_compliance_issues = await self.check_legal_compliance(text)
        
        # Calculer un score de conformité global
        total_issues = len(spelling_errors) + len(grammar_errors) + len(legal_compliance_issues)
        compliance_score = max(0.0, 1.0 - (total_issues / 100)) if total_issues > 0 else 1.0        # Générer des suggestions d'amélioration
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
        Vérifie l'orthographe du texte avec un correcteur orthographique avancé.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste d'erreurs d'orthographe
        """
        errors = []
        
        # Tokeniser le texte en mots
        words = re.findall(r'\b[a-zA-ZàâäéèêëïîôöùûüçÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]+\b', text)
        
        # Vérifier chaque mot
        for i, word in enumerate(words):
            # Ignorer les mots très courts et les termes juridiques connus
            if len(word) < 3 or word.lower() in [term.lower() for term in self.legal_terms]:
                continue
                
            # Vérifier avec le correcteur orthographique
            if word.lower() not in self.spell_checker:
                # Trouver la position du mot dans le texte original
                pattern = r'\b' + re.escape(word) + r'\b'
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                if matches:
                    match = matches[0] if len(matches) == 1 else matches[min(i, len(matches)-1)]
                    position = {"start": match.start(), "end": match.end()}
                    
                    # Obtenir des suggestions de correction
                    candidates = self.spell_checker.candidates(word.lower())
                    suggestions = list(candidates)[:3] if candidates else []
                    
                    # Vérifier avec le dictionnaire de corrections personnalisé
                    if word.lower() in self.common_corrections:
                        suggestions.insert(0, self.common_corrections[word.lower()])
                    
                    if suggestions:  # Seulement ajouter si on a des suggestions
                        errors.append(
                            SpellingError(
                                word=word,
                                position=position,
                                suggestions=suggestions
                            )
                        )
        
        return errors
        
    def check_grammar(self, text: str) -> List[GrammarError]:
        """
        Vérifie la grammaire du texte avec LanguageTool.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste d'erreurs grammaticales
        """
        errors = []
        
        try:
            # Utiliser LanguageTool pour la vérification grammaticale
            matches = self.grammar_tool.check(text)
            
            for match in matches:
                # Filtrer les erreurs non pertinentes (orthographe déjà vérifiée ailleurs)
                if match.category in ['TYPOS', 'SPELLING']:
                    continue
                    
                error = GrammarError(
                    text=text[match.offset:match.offset + match.errorLength],
                    position={"start": match.offset, "end": match.offset + match.errorLength},
                    message=match.message,
                    suggestions=match.replacements[:3]  # Limiter à 3 suggestions
                )
                errors.append(error)
                
        except Exception as e:
            print(f"Erreur lors de la vérification grammaticale: {e}")
            # Fallback vers l'ancienne méthode si LanguageTool échoue
            errors = self._check_grammar_fallback(text)
            
        return errors
    
    def _check_grammar_fallback(self, text: str) -> List[GrammarError]:
        """
        Méthode de fallback pour la vérification grammaticale basée sur spaCy.
        """
        doc = self.nlp(text)
        errors = []
        
        for i, token in enumerate(doc):
            if token.is_alpha and i > 0:
                # Vérifier les accords simples
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
        
    async def check_legal_compliance(self, text: str) -> List[LegalComplianceIssue]:
        """
        Vérifie la conformité légale du texte en analysant avec la base de connaissances.
        
        Args:
            text: Le texte à vérifier
            
        Returns:
            Une liste de problèmes de conformité légale
        """
        issues = []
        
        # 1. Vérifications automatiques de base
        issues.extend(self._check_basic_legal_requirements(text))
        
        # 2. Analyse avancée avec la base de connaissances
        try:
            legal_analysis = await self._analyze_with_knowledge_base(text)
            issues.extend(legal_analysis)
        except Exception as e:
            print(f"Erreur lors de l'analyse juridique avancée: {e}")
        
        return issues
    
    def _check_basic_legal_requirements(self, text: str) -> List[LegalComplianceIssue]:
        """
        Vérifie les exigences légales de base.
        """
        issues = []
        text_lower = text.lower()
        
        # Vérifier la présence de termes juridiques importants
        missing_terms = []
        for term in self.legal_terms:
            if term not in text_lower:
                missing_terms.append(term)
        
        if len(missing_terms) > len(self.legal_terms) * 0.7:  # Si plus de 70% des termes manquent
            issues.append(
                LegalComplianceIssue(
                    text="",
                    position={"start": 0, "end": 0},
                    issue_type="Termes juridiques manquants",
                    description=f"Document incomplet : plusieurs termes juridiques importants sont absents. Exemples manquants : {', '.join(missing_terms[:5])}",
                    recommendation="Ajoutez les termes juridiques appropriés selon le type de document (contrat, statuts, etc.)."
                )
            )
        
        # Vérifications spécifiques selon le contenu
        if "tva" in text_lower and "numéro de tva" not in text_lower and "tva intracommunautaire" not in text_lower:
            tva_pos = text_lower.find("tva")
            issues.append(
                LegalComplianceIssue(
                    text="TVA",
                    position={"start": tva_pos, "end": tva_pos + 3},
                    issue_type="Mention légale incomplète",
                    description="La TVA est mentionnée mais le numéro de TVA intracommunautaire n'est pas précisé.",
                    recommendation="Ajoutez le numéro de TVA intracommunautaire de votre Junior-Entreprise."
                )
            )
        
        # Vérifier les mentions obligatoires pour les contrats
        if any(word in text_lower for word in ["contrat", "prestation", "service"]):
            contract_issues = self._check_contract_requirements(text)
            issues.extend(contract_issues)
        
        # Vérifier les statuts d'association
        if any(word in text_lower for word in ["statuts", "association", "assemblée"]):
            statute_issues = self._check_statute_requirements(text)
            issues.extend(statute_issues)
        
        return issues
    
    def _check_contract_requirements(self, text: str) -> List[LegalComplianceIssue]:
        """
        Vérifie les exigences spécifiques aux contrats.
        """
        issues = []
        text_lower = text.lower()
        
        required_clauses = [
            ("responsabilité civile", "clause de responsabilité civile"),
            ("conditions générales", "conditions générales de vente/prestation"),
            ("délai", "délais d'exécution"),
            ("paiement", "conditions de paiement"),
            ("propriété intellectuelle", "clause de propriété intellectuelle")
        ]
        
        for clause, description in required_clauses:
            if clause not in text_lower:
                issues.append(
                    LegalComplianceIssue(
                        text="",
                        position={"start": 0, "end": 0},
                        issue_type="Clause contractuelle manquante",
                        description=f"Clause manquante : {description}",
                        recommendation=f"Ajoutez une {description} dans votre contrat."
                    )
                )
        
        return issues
    
    def _check_statute_requirements(self, text: str) -> List[LegalComplianceIssue]:
        """
        Vérifie les exigences spécifiques aux statuts d'association.
        """
        issues = []
        text_lower = text.lower()
        
        required_elements = [
            ("objet social", "définition de l'objet social"),
            ("siège social", "adresse du siège social"),
            ("conseil d'administration", "composition du conseil d'administration"),
            ("assemblée générale", "modalités d'assemblée générale"),
            ("dissolution", "conditions de dissolution")
        ]
        
        for element, description in required_elements:
            if element not in text_lower:
                issues.append(
                    LegalComplianceIssue(
                        text="",
                        position={"start": 0, "end": 0},
                        issue_type="Élément statutaire manquant",
                        description=f"Élément manquant : {description}",
                        recommendation=f"Les statuts doivent inclure {description}."
                    )
                )
        
        return issues
    
    async def _analyze_with_knowledge_base(self, text: str) -> List[LegalComplianceIssue]:
        """
        Analyse le document avec la base de connaissances juridique.
        """
        issues = []
        
        try:
            # Préparer la requête pour l'analyse juridique
            legal_query = f"""
            Analysez ce document du point de vue juridique en vous basant sur votre base de connaissances sur les Junior-Entreprises.
            Identifiez les éléments non conformes au droit français et aux spécificités des Junior-Entreprises.
            
            Document à analyser :
            {text[:2000]}  # Limiter à 2000 caractères pour éviter les requêtes trop longues
            
            Recherchez spécifiquement :
            1. Les mentions légales obligatoires manquantes
            2. Les clauses contractuelles non conformes
            3. Les éléments statutaires incorrects
            4. Les obligations fiscales et sociales non respectées
            5. Citez les sources juridiques pertinentes de votre base de connaissances
            """
            
            # Utiliser le service de chat pour analyser avec la base de connaissances
            from app.schemas.chat import ChatRequest
            
            chat_request = ChatRequest(message=legal_query)
            
            # Créer une conversation temporaire pour l'analyse
            temp_conversation_id = f"legal_analysis_{uuid.uuid4()}"
            
            # Analyser avec le service de chat (qui utilise la base de connaissances)
            response = await self.chat_service.process_query(
                request=chat_request,
                conversation_id=temp_conversation_id,
                user_id=1  # Utilisateur système pour l'analyse
            )
            
            # Parser la réponse pour extraire les problèmes juridiques
            if response and response.response:
                legal_issues = self._parse_legal_analysis_response(response.response)
                issues.extend(legal_issues)
        
        except Exception as e:
            print(f"Erreur lors de l'analyse avec la base de connaissances: {e}")
            # En cas d'erreur, ajouter un conseil général
            issues.append(
                LegalComplianceIssue(
                    text="",
                    position={"start": 0, "end": 0},
                    issue_type="Analyse juridique recommandée",
                    description="Une analyse juridique approfondie est recommandée pour ce document.",
                    recommendation="Consultez un expert juridique ou votre référent CNJE pour valider la conformité de ce document."
                )
            )
        
        return issues
    
    def _parse_legal_analysis_response(self, response_text: str) -> List[LegalComplianceIssue]:
        """
        Parse la réponse de l'analyse juridique pour extraire les problèmes.
        """
        issues = []
        
        # Rechercher des mots-clés indiquant des problèmes juridiques
        problem_indicators = [
            "manque", "manquant", "absent", "non conforme", "incorrecte", 
            "obligatoire", "doit", "devrait", "nécessaire", "requis"
        ]
        
        sentences = response_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in problem_indicators):
                # Extraire le type de problème et la recommandation
                issue_type = "Problème juridique identifié"
                description = sentence
                recommendation = "Consultez votre base de connaissances juridique ou un expert."
                
                # Chercher des sources dans la réponse
                if "source" in sentence.lower() or "article" in sentence.lower() or "loi" in sentence.lower():
                    recommendation = f"Référence juridique trouvée dans la base : {sentence}"
                
                issues.append(
                    LegalComplianceIssue(
                        text="",
                        position={"start": 0, "end": 0},
                        issue_type=issue_type,
                        description=description,
                        recommendation=recommendation
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
        
        # Suggestions basées sur les erreurs d'orthographe
        if spelling_errors:
            suggestions.append(f"Corrigez les {len(spelling_errors)} erreurs d'orthographe identifiées.")
        
        # Suggestions basées sur les erreurs grammaticales
        if grammar_errors:
            suggestions.append(f"Corrigez les {len(grammar_errors)} erreurs grammaticales identifiées.")
        
        # Suggestions basées sur les problèmes de conformité légale
        for issue in legal_issues:
            suggestions.append(issue.recommendation)
        
        # Suggestions générales
        if "junior entreprise" not in text.lower():
            suggestions.append("Mentionnez explicitement 'Junior Entreprise' dans votre document.")
        
        if "CNJE" not in text:
            suggestions.append("Considérez mentionner la CNJE (Confédération Nationale des Junior-Entreprises).")
        
        return suggestions
    async def auto_correct_document(self, document_id: str) -> dict:
        """
        Corrige automatiquement les erreurs d'orthographe et de grammaire dans un document.
        
        Args:
            document_id: L'identifiant du document à corriger
            
        Returns:
            Un dictionnaire contenant les informations sur la correction
        """
        # Trouver le document
        file_path, filename = self.find_document_by_id(document_id)
        
        if not file_path:
            raise FileNotFoundError(f"Document avec l'ID {document_id} non trouvé")
            
        # Extraire le texte du document
        original_text = self.extract_text(file_path)
        
        # Analyser le texte pour trouver les erreurs
        spelling_errors = self.check_spelling(original_text)
        grammar_errors = self.check_grammar(original_text)
        legal_compliance_issues = await self.check_legal_compliance(original_text)
        
        # Corriger le texte
        corrected_text = original_text
        corrections_details = []
        
        # 1. Corriger les erreurs d'orthographe évidentes
        for error in spelling_errors:
            word = error.word
            if suggestions := error.suggestions:
                replacement = suggestions[0]
                if word.lower() in self.common_corrections:
                    replacement = self.common_corrections[word.lower()]
                
                old_text = corrected_text
                corrected_text = corrected_text.replace(word, replacement)
                
                if old_text != corrected_text:
                    corrections_details.append(f"Correction orthographique: '{word}' → '{replacement}'")
        
        # 2. Corriger les erreurs grammaticales basiques
        for error in grammar_errors:
            if len(error.suggestions) > 0:
                old_text = corrected_text
                corrected_text = corrected_text.replace(error.text, error.suggestions[0])
                
                if old_text != corrected_text:
                    corrections_details.append(f"Correction grammaticale: '{error.text}' → '{error.suggestions[0]}'")
        
        # 3. Vérifier et signaler les problèmes juridiques qui ne peuvent pas être corrigés automatiquement
        legal_recommendations = []
        for issue in legal_compliance_issues:
            legal_recommendations.append(f"{issue.issue_type}: {issue.description} - {issue.recommendation}")
        
        # 4. Enregistrer le document corrigé
        # Déterminer l'extension du fichier
        _, ext = os.path.splitext(filename)
        corrected_id = f"{document_id}_corrected"
        corrected_file_path = os.path.join(self.upload_dir, f"{corrected_id}{ext}")
        
        # Enregistrer le texte corrigé avec support multiformat amélioré
        if ext.lower() == ".txt":
            with open(corrected_file_path, "w", encoding="utf-8") as f:
                f.write(corrected_text)
        elif ext.lower() in [".docx", ".doc"]:
            # Pour les documents Word, on crée un nouveau document texte
            # Dans une implémentation réelle, on utiliserait python-docx pour conserver le formatage
            with open(corrected_file_path.replace(ext, ".txt"), "w", encoding="utf-8") as f:
                f.write(corrected_text)
                corrected_file_path = corrected_file_path.replace(ext, ".txt")
                ext = ".txt"
        else:
            # Pour les autres formats, nous créons un fichier texte
            with open(corrected_file_path.replace(ext, ".txt"), "w", encoding="utf-8") as f:
                f.write(corrected_text)
                corrected_file_path = corrected_file_path.replace(ext, ".txt")
                ext = ".txt"
        
        # Retourner les informations sur la correction
        return {
            "original_document_id": document_id,
            "corrected_document_id": corrected_id,
            "filename": f"{corrected_id}{ext}",
            "corrections_applied": len(corrections_details),
            "corrections_details": corrections_details,
            "legal_recommendations": legal_recommendations,
            "status": "corrected",
            "file_path": corrected_file_path
        }

    def process_document(self, content: bytes, filename: str) -> dict:
        """
        Traite un document et retourne les résultats de l'analyse.
        
        Args:
            content: Le contenu du fichier en bytes.
            filename: Le nom du fichier.
        
        Returns:
            Un dictionnaire contenant les résultats de l'analyse.
        """
        # Exemple de traitement (à adapter selon vos besoins)
        return {"filename": filename, "status": "processed"}