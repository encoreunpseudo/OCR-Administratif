import pandas as pd
import os
import json
from datetime import datetime

class OutputManager:
    def __init__(self, output_dir='output'):
        """Initialise le gestionnaire de sortie"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save_to_csv(self, data_list, filename=None):
        """Enregistre les données extraites au format CSV"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'extracted_data_{timestamp}.csv'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convertir en DataFrame pandas
        df = pd.DataFrame(data_list)
        
        # Enregistrer en CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')  # utf-8-sig pour Excel
        print(f"Données enregistrées dans {filepath}")
        
        return filepath
    
    def save_to_excel(self, data_list, filename=None):
        """Enregistre les données extraites au format Excel"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'extracted_data_{timestamp}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convertir en DataFrame pandas
        df = pd.DataFrame(data_list)
        
        # Enregistrer en Excel
        df.to_excel(filepath, index=False)
        print(f"Données enregistrées dans {filepath}")
        
        return filepath
    
    def save_to_json(self, data_list, filename=None):
        """Enregistre les données extraites au format JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'extracted_data_{timestamp}.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Enregistrer en JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=4)
        
        print(f"Données enregistrées dans {filepath}")
        
        return filepath
    
    def get_all_outputs(self):
        """Récupère tous les fichiers de sortie disponibles"""
        files = []
        
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath):
                    file_info = {
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Déterminer le type de fichier
                    if filename.endswith('.csv'):
                        file_info['type'] = 'csv'
                    elif filename.endswith('.xlsx'):
                        file_info['type'] = 'excel'
                    elif filename.endswith('.json'):
                        file_info['type'] = 'json'
                    else:
                        file_info['type'] = 'unknown'
                        
                    files.append(file_info)
        
        # Trier par date de modification (le plus récent d'abord)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return files