import base64
import requests
import json
import os
from PIL import Image
import io
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class FollicleStage(Enum):
    PRIMORDIAL = "primordial"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ANTRAL = "antral"
    PREOVULATORY = "preovulatory"
    CORPUS_LUTEUM = "corpus_luteum"

class HysteroscopyFinding(Enum):
    NORMAL = "normal"
    POLYP = "polyp"
    FIBROID = "fibroid"
    ADHESION = "adhesion"
    SEPTUM = "septum"
    HYPERPLASIA = "hyperplasia"
    ATROPHY = "atrophy"

@dataclass
class FollicleAnalysis:
    scan_id: str
    patient_id: str
    ovary_side: str  # left/right/bilateral
    total_follicle_count: int
    antral_follicle_count: int
    dominant_follicle_size: float  # mm
    follicle_sizes: List[float]  # all measured follicles
    ovarian_volume: float  # ml
    stromal_echogenicity: str  # normal/increased/decreased
    blood_flow: str  # normal/increased/decreased
    classification: str
    amh_correlation: str
    ivf_prognosis: str
    notes: str
    timestamp: str

@dataclass
class HysteroscopyAnalysis:
    procedure_id: str
    patient_id: str
    uterine_cavity: str  # normal/abnormal
    endometrial_thickness: float  # mm
    endometrial_pattern: str  # proliferative/secretory/atrophic
    cervical_canal: str  # normal/stenotic/dilated
    tubal_ostia: str  # bilateral_patent/unilateral_patent/bilateral_blocked
    pathological_findings: List[HysteroscopyFinding]
    lesion_locations: List[str]
    lesion_sizes: List[float]
    vascularization: str  # normal/increased/decreased
    classification: str
    treatment_recommendation: str
    biopsy_indicated: bool
    notes: str
    timestamp: str

class UltrasoundAnalyzer:
    def __init__(self, deepseek_api_key: str = None, deepseek_url: str = "http://localhost:11434/api/generate"):
        """Initialize ultrasound analyzer with DeepSeek LLM"""
        self.deepseek_url = deepseek_url
        self.api_key = deepseek_api_key
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 for LLM processing"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def preprocess_ultrasound_image(self, image_path: str, scan_type: str) -> str:
        """Preprocess ultrasound images for better analysis"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return image_path
            
            if scan_type == "follicle":
                # Enhance contrast for follicle detection
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # Apply CLAHE for better contrast
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                # Convert back to BGR
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
                
            elif scan_type == "hysteroscopy":
                # Enhance for endometrial structure visibility
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
                
            else:
                enhanced = image
            
            # Save preprocessed image (robust path handling)
            base, ext = os.path.splitext(image_path)
            processed_path = f"{base}_processed{ext}"
            cv2.imwrite(processed_path, enhanced)
            
            return processed_path
        except Exception as e:
            print(f"Error preprocessing ultrasound image: {e}")
            return image_path

    def analyze_follicle_scan(self, image_path: str, ovary_side: str = "bilateral") -> Dict:
        """Analyze follicle ultrasound scan using DeepSeek LLM"""
        try:
            processed_image = self.preprocess_ultrasound_image(image_path, "follicle")
            base64_image = self.encode_image_to_base64(processed_image)
            
            prompt = f"""
            You are an expert reproductive endocrinologist analyzing an ovarian follicle ultrasound scan. Please analyze this {ovary_side} ovarian ultrasound image and provide detailed assessment:

            FOLLICLE SCAN ANALYSIS REPORT:
            
            1. FOLLICLE COUNT AND ASSESSMENT:
            - Total visible follicles: [count all visible follicles]
            - Antral follicle count (2-10mm): [count AFC]
            - Small follicles (<2mm): [count]
            - Medium follicles (10-18mm): [count]
            - Large follicles (>18mm): [count]
            - Dominant follicle size: [largest follicle in mm]
            
            2. FOLLICLE MEASUREMENTS:
            - List all measurable follicle diameters: [e.g., 15mm, 12mm, 8mm, etc.]
            - Follicle distribution: [uniform/clustered/peripheral]
            - Follicle morphology: [round/oval/irregular]
            
            3. OVARIAN ASSESSMENT:
            - Ovarian volume estimate: [length × width × height × 0.523 in ml]
            - Ovarian shape: [normal/enlarged/atrophic]
            - Stromal echogenicity: [normal/increased/decreased]
            - Stromal texture: [homogeneous/heterogeneous]
            
            4. VASCULAR ASSESSMENT:
            - Ovarian blood flow: [normal/increased/decreased]
            - Follicular blood flow: [present/absent around dominant follicle]
            - Stromal vascularity: [normal/increased/decreased]
            
            5. CYCLE ASSESSMENT:
            - Estimated cycle phase: [follicular/ovulatory/luteal]
            - Ovulation prediction: [imminent/24-48hrs/not predicted]
            - Corpus luteum: [present/absent/size if present]
            
            6. CLINICAL CORRELATION:
            - AFC category: [low <5/normal 5-15/high >15]
            - Ovarian reserve assessment: [poor/normal/high]
            - PCOS indicators: [present/absent - multiple small follicles, stromal changes]
            - IVF stimulation prediction: [poor/normal/high responder]
            
            7. RECOMMENDATIONS:
            - AMH correlation suggested: [yes/no]
            - Follow-up timing: [days]
            - Additional imaging needed: [yes/no]
            - Clinical action: [continue monitoring/trigger ovulation/adjust medication]
            
            Please provide specific measurements and counts based on visual assessment of the ultrasound image.
            """
            
            return self._query_deepseek(prompt, base64_image)
        except Exception as e:
            return {
                "success": False,
                "error": f"Follicle scan analysis failed: {str(e)}",
                "analysis": ""
            }

    def analyze_hysteroscopy_image(self, image_path: str) -> Dict:
        """Analyze hysteroscopy image using DeepSeek LLM"""
        try:
            processed_image = self.preprocess_ultrasound_image(image_path, "hysteroscopy")
            base64_image = self.encode_image_to_base64(processed_image)
            
            prompt = """
            You are an expert gynecologist analyzing a hysteroscopy image. Please analyze this endometrial/uterine cavity image and provide detailed assessment:

            HYSTEROSCOPY ANALYSIS REPORT:
            
            1. UTERINE CAVITY ASSESSMENT:
            - Cavity shape: [triangular/irregular/distorted]
            - Cavity size: [normal/enlarged/small]
            - Cavity walls: [smooth/irregular/nodular]
            - Fundal contour: [normal/indented/irregular]
            
            2. ENDOMETRIAL ASSESSMENT:
            - Endometrial thickness: [estimate in mm]
            - Endometrial pattern: [proliferative/secretory/atrophic/hyperplastic]
            - Endometrial color: [pink/pale/red/white]
            - Endometrial texture: [smooth/rough/irregular]
            - Glandular openings: [visible/not visible]
            
            3. CERVICAL CANAL:
            - Canal appearance: [normal/stenotic/dilated]
            - Canal walls: [smooth/irregular]
            - Cervical mucus: [present/absent/amount]
            
            4. TUBAL OSTIA:
            - Right ostium: [visible/patent/blocked/not visualized]
            - Left ostium: [visible/patent/blocked/not visualized]
            - Ostial appearance: [normal/inflamed/stenotic]
            
            5. PATHOLOGICAL FINDINGS:
            - Polyps: [present/absent - if present: number, size, location]
            - Fibroids: [present/absent - if present: type, size, location]
            - Adhesions: [present/absent - if present: extent, location]
            - Septum: [present/absent - if present: complete/incomplete]
            - Hyperplasia: [present/absent - if present: focal/diffuse]
            - Other lesions: [describe any other abnormalities]
            
            6. VASCULAR ASSESSMENT:
            - Endometrial vascularity: [normal/increased/decreased]
            - Abnormal vessels: [present/absent]
            - Bleeding: [present/absent/location]
            
            7. OVERALL ASSESSMENT:
            - Cavity classification: [normal/abnormal]
            - Primary diagnosis: [normal/polyp/fibroid/adhesions/septum/hyperplasia/other]
            - Severity: [mild/moderate/severe if abnormal]
            
            8. CLINICAL RECOMMENDATIONS:
            - Biopsy indicated: [yes/no - specify location if yes]
            - Treatment needed: [none/polypectomy/myomectomy/adhesiolysis/septoplasty/other]
            - Follow-up required: [yes/no - timing if yes]
            - Fertility impact: [none/mild/moderate/severe]
            
            Please provide specific measurements and detailed descriptions based on visual assessment.
            """
            
            return self._query_deepseek(prompt, base64_image)
        except Exception as e:
            return {
                "success": False,
                "error": f"Hysteroscopy analysis failed: {str(e)}",
                "analysis": ""
            }

    def _query_deepseek(self, prompt: str, base64_image: str) -> Dict:
        """Query DeepSeek LLM with image and prompt"""
        try:
            payload = {
                "model": "deepseek-coder",
                "prompt": prompt,
                "images": [base64_image],
                "stream": False
            }
            
            response = requests.post(
                self.deepseek_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for complex analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "analysis": result.get("response", ""),
                    "model": "deepseek"
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "analysis": ""
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "DeepSeek LLM not available. Please start Ollama service.",
                "analysis": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": ""
            }
