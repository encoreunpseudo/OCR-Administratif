import re
import datetime

class DataExtractor:
    def __init__(self, document_type):
        """Initialise l'extracteur de données avec un type de document"""
        self.document_type = document_type
        
    def extract_data(self, text):
        """Extrait les données structurées du texte selon le type de document"""
        if self.document_type == 'ticket':
            return self._extract_from_ticket(text)
        elif self.document_type == 'facture':
            return self._extract_from_facture(text)
        elif self.document_type == 'releve':
            return self._extract_from_releve(text)
        else:
            raise ValueError(f"Type de document non pris en charge: {self.document_type}")
    
    def _extract_from_ticket(self, text):
        """Extrait les données d'un ticket de caisse"""
        data = {
            'type_document': 'ticket',
            'texte_brut': text
        }
        
        # Recherche de la date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Format: DD/MM/YYYY ou DD-MM-YYYY
            r'(\d{1,2} [a-zA-Z]{3,9} \d{2,4})',   # Format: DD MOIS YYYY
            r'(\d{2}[/-]\d{2}[/-]\d{2,4})'        # Format: DD/MM/YY
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                data['date'] = date_match.group(0)
                break
        
        # Recherche heure
        time_pattern = r'(\d{1,2}[:hH]\d{2}(?:[:]\d{2})?)'
        time_match = re.search(time_pattern, text)
        if time_match:
            data['heure'] = time_match.group(0)
        
        # Recherche montant total
        total_patterns = [
            r'total[:\s]*(\d+[.,]\d{2})',
            r'montant[:\s]*(\d+[.,]\d{2})',
            r'net à payer[:\s]*(\d+[.,]\d{2})',
            r'total ttc[:\s]*(\d+[.,]\d{2})'
        ]
        
        for pattern in total_patterns:
            total_match = re.search(pattern, text, re.IGNORECASE)
            if total_match:
                data['montant_total'] = total_match.group(1).replace(',', '.')
                break
        
        # Recherche du nom du commerce
        # Souvent les 1-2 premières lignes du ticket
        lines = text.strip().split('\n')
        if lines:
            data['commerce'] = lines[0].strip()
            
            # Si la première ligne semble trop courte ou non pertinente
            if len(data['commerce']) < 3 and len(lines) > 1:
                data['commerce'] = lines[1].strip()
        
        # Recherche de numéro TVA/SIRET
        tva_pattern = r'(FR\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{3})'
        tva_match = re.search(tva_pattern, text)
        if tva_match:
            data['numero_tva'] = tva_match.group(0).replace(' ', '')
            
        siret_pattern = r'siret[:\s]*(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})'
        siret_match = re.search(siret_pattern, text, re.IGNORECASE)
        if siret_match:
            data['siret'] = siret_match.group(1).replace(' ', '')
        
        return data
    
    def _extract_from_facture(self, text):
        """Extrait les données d'une facture"""
        data = {
            'type_document': 'facture',
            'texte_brut': text
        }
        
        # Numéro de facture
        facture_num_patterns = [
            r'facture[:\s]*n?[°o]?[:\s]*(\w+[-/]?\w+)',
            r'n°\s?(?:facture|fact)[:\s]*(\w+[-/]?\w+)',
            r'(?:facture|fact)[:\s]*n?[°o]?[:\s]*(\d+)'
        ]
        
        for pattern in facture_num_patterns:
            num_match = re.search(pattern, text, re.IGNORECASE)
            if num_match:
                data['num_facture'] = num_match.group(1)
                break
        
        # Date de facture
        date_patterns = [
            r'date[:\s]*(?:de facture|facture|d\'émission)?[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'factur[ée] le[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'émis le[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                data['date_facture'] = date_match.group(1)
                break
        
        # Montant HT
        ht_patterns = [
            r'total\s?h\.?t\.?[:\s]*(\d+[.,]\d{2})',
            r'montant\s?h\.?t\.?[:\s]*(\d+[.,]\d{2})',
            r'h\.?t\.?[:\s]*(\d+[.,]\d{2})'
        ]
        
        for pattern in ht_patterns:
            ht_match = re.search(pattern, text, re.IGNORECASE)
            if ht_match:
                data['montant_ht'] = ht_match.group(1).replace(',', '.')
                break
        
        # TVA
        tva_patterns = [
            r'tva[:\s]*(\d+[.,]\d{2})',
            r'total\s?tva[:\s]*(\d+[.,]\d{2})',
            r'montant\s?tva[:\s]*(\d+[.,]\d{2})'
        ]
        
        for pattern in tva_patterns:
            tva_match = re.search(pattern, text, re.IGNORECASE)
            if tva_match:
                data['montant_tva'] = tva_match.group(1).replace(',', '.')
                break
        
        # Montant TTC
        ttc_patterns = [
            r'total\s?t\.?t\.?c\.?[:\s]*(\d+[.,]\d{2})',
            r'montant\s?t\.?t\.?c\.?[:\s]*(\d+[.,]\d{2})',
            r't\.?t\.?c\.?[:\s]*(\d+[.,]\d{2})'
        ]
        
        for pattern in ttc_patterns:
            ttc_match = re.search(pattern, text, re.IGNORECASE)
            if ttc_match:
                data['montant_ttc'] = ttc_match.group(1).replace(',', '.')
                break
        
        # Émetteur de la facture (vendeur)
        # Généralement dans les premières lignes
        lines = text.strip().split('\n')
        top_lines = ' '.join(lines[:5])
        
        # Essayer de trouver le nom de l'entreprise
        company_pattern = r'([\w\s]{2,30}?)\s(?:SARL|SAS|SA|EURL|EI|SASU)'
        company_match = re.search(company_pattern, top_lines)
        if company_match:
            data['emetteur'] = company_match.group(0)
        elif len(lines) > 0:
            data['emetteur'] = lines[0].strip()
        
        return data
    
    def _extract_from_releve(self, text):
        """Extrait les données d'un relevé bancaire"""
        data = {
            'type_document': 'releve',
            'texte_brut': text
        }
        
        # Recherche du nom de la banque
        bank_patterns = [
            r'(banque populaire|crédit agricole|bnp paribas|société générale|caisse d\'épargne|crédit mutuel|lcl|la banque postale|cic|hsbc)',
            r'(boursorama|fortuneo|ing|monabanq|hello bank|n26|revolut)'
        ]
        
        for pattern in bank_patterns:
            bank_match = re.search(pattern, text, re.IGNORECASE)
            if bank_match:
                data['banque'] = bank_match.group(0).title()  # Mettre en majuscule la première lettre
                break
        
        # Recherche de période du relevé
        period_patterns = [
            r'relevé du (\d{1,2}[/-]\d{1,2}[/-]\d{2,4}) au (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'période du (\d{1,2}[/-]\d{1,2}[/-]\d{2,4}) au (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in period_patterns:
            period_match = re.search(pattern, text, re.IGNORECASE)
            if period_match:
                data['date_debut'] = period_match.group(1)
                data['date_fin'] = period_match.group(2)
                break
        
        # Recherche du numéro de compte
        account_patterns = [
            r'compte n°[:\s]*([0-9x]{4,})',
            r'n° de compte[:\s]*([0-9x]{4,})',
            r'rib[:\s]*([0-9]{4,})'
        ]
        
        for pattern in account_patterns:
            account_match = re.search(pattern, text, re.IGNORECASE)
            if account_match:
                data['numero_compte'] = account_match.group(1)
                break
        
        # Recherche du solde
        balance_patterns = [
            r'solde (?:final|au \d{1,2}[/-]\d{1,2}[/-]\d{2,4})[:\s]*(-?\d+[.,]\d{2})',
            r'nouveau solde[:\s]*(-?\d+[.,]\d{2})',
            r'solde créditeur[:\s]*(\d+[.,]\d{2})',
            r'solde débiteur[:\s]*(-\d+[.,]\d{2})'
        ]
        
        for pattern in balance_patterns:
            balance_match = re.search(pattern, text, re.IGNORECASE)
            if balance_match:
                data['solde'] = balance_match.group(1).replace(',', '.')
                break
        
        return data