import cv2
import pytesseract
from PIL import Image
import numpy as np
import os

class OCREngine:
    def __init__(self, lang='fra+eng'):
        self.lang = lang
        
    def preprocess_image(self, img):
        """Prétraitement de l'image pour améliorer la reconnaissance OCR"""
        if isinstance(img, str):
            img = cv2.imread(img)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def extract_text(self, img_path):
        """Extrait le texte d'une image"""
        # Vérifier si le chemin existe
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Le fichier {img_path} n'existe pas")
        
        # Lire l'image
        img = cv2.imread(img_path)
        
        # Prétraitement
        preprocessed_img = self.preprocess_image(img)
        
        # OCR avec Tesseract
        text = pytesseract.image_to_string(
            Image.fromarray(preprocessed_img), 
            lang=self.lang
        )
        
        # Sauvegarder l'image prétraitée pour le débogage (facultatif)
        debug_path = img_path.replace('.', '_preprocessed.')
        cv2.imwrite(debug_path, preprocessed_img)
        
        return text
    
    def extract_text_and_layout(self, img_path):
        """Extrait le texte et les informations de mise en page"""
        # Prétraitement comme avant
        img = cv2.imread(img_path)
        preprocessed_img = self.preprocess_image(img)
        
        # Obtenir les données de mise en page
        d = pytesseract.image_to_data(
            Image.fromarray(preprocessed_img),
            lang=self.lang,
            output_type=pytesseract.Output.DICT
        )
        
        # Obtenir simplement le texte aussi
        text = pytesseract.image_to_string(
            Image.fromarray(preprocessed_img),
            lang=self.lang
        )
        
        return text, d