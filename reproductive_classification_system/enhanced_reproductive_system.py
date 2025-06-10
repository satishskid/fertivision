import os
import sqlite3
import datetime
import json
from typing import Dict
from werkzeug.utils import secure_filename
from reproductive_classification_system import ReproductiveClassificationSystem, OocyteMaturity
from image_analysis import ImageAnalyzer
import re
from ultrasound_analysis import UltrasoundAnalyzer, FollicleAnalysis, HysteroscopyAnalysis, FollicleStage, HysteroscopyFinding

class EnhancedReproductiveSystem(ReproductiveClassificationSystem):
    def __init__(self, db_path: str = "reproductive_analysis.db", upload_folder: str = "uploads"):
        super().__init__(db_path)
        self.upload_folder = upload_folder
        self.image_analyzer = ImageAnalyzer()
        self.ultrasound_analyzer = UltrasoundAnalyzer()  # Add ultrasound analyzer
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'dcm'}  # Add DICOM support
        # Create upload directory
        os.makedirs(upload_folder, exist_ok=True)
        # Add image analysis table to database
        self._init_image_tables()
    def _init_image_tables(self):
        """Initialize tables for image analysis storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Existing tables...
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT,
                analysis_type TEXT,
                image_path TEXT,
                llm_analysis TEXT,
                processed_data TEXT,
                timestamp TEXT
            )
        ''')
        # Add ultrasound analysis tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follicle_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hysteroscopy_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                procedure_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    def analyze_sperm_with_image(self, image_path: str, **kwargs) -> dict:
        image_result = self.image_analyzer.analyze_sperm_image(image_path)
        if image_result["success"]:
            llm_analysis = image_result["analysis"]
            extracted_params = self._extract_sperm_parameters(llm_analysis)
            merged_params = {**extracted_params, **kwargs}
            classification_result = self.classify_sperm(**merged_params)
            self._store_image_analysis(
                classification_result.sample_id,
                "sperm",
                image_path,
                llm_analysis,
                merged_params
            )
            classification_result.image_analysis = llm_analysis
            classification_result.image_path = image_path
            return classification_result
        else:
            raise Exception(f"Image analysis failed: {image_result['error']}")
    def analyze_oocyte_with_image(self, image_path: str, **kwargs) -> dict:
        image_result = self.image_analyzer.analyze_oocyte_image(image_path)
        if image_result["success"]:
            llm_analysis = image_result["analysis"]
            extracted_params = self._extract_oocyte_parameters(llm_analysis)
            merged_params = {**extracted_params, **kwargs}
            classification_result = self.classify_oocyte(**merged_params)
            self._store_image_analysis(
                classification_result.oocyte_id,
                "oocyte",
                image_path,
                llm_analysis,
                merged_params
            )
            classification_result.image_analysis = llm_analysis
            classification_result.image_path = image_path
            return classification_result
        else:
            raise Exception(f"Image analysis failed: {image_result['error']}")
    def analyze_embryo_with_image(self, image_path: str, day: int, **kwargs) -> dict:
        image_result = self.image_analyzer.analyze_embryo_image(image_path, day)
        if image_result["success"]:
            llm_analysis = image_result["analysis"]
            extracted_params = self._extract_embryo_parameters(llm_analysis, day)
            merged_params = {**extracted_params, **kwargs}
            merged_params['day'] = day
            classification_result = self.classify_embryo(**merged_params)
            self._store_image_analysis(
                classification_result.embryo_id,
                "embryo",
                image_path,
                llm_analysis,
                merged_params
            )
            classification_result.image_analysis = llm_analysis
            classification_result.image_path = image_path
            return classification_result
        else:
            raise Exception(f"Image analysis failed: {image_result['error']}")
    def _extract_sperm_parameters(self, llm_analysis: str) -> dict:
        params = {}
        lines = llm_analysis.split('\n')
        for line in lines:
            if 'concentration' in line.lower() and 'million/ml' in line.lower():
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*million/ml', line)
                    if match:
                        params['concentration'] = float(match.group(1))
                except:
                    pass
            if 'progressive motility' in line.lower() and '%' in line:
                try:
                    match = re.search(r'(\d+\.?\d*)\s*%', line)
                    if match:
                        params['progressive_motility'] = float(match.group(1))
                except:
                    pass
            if 'normal morphology' in line.lower() and '%' in line:
                try:
                    match = re.search(r'(\d+\.?\d*)\s*%', line)
                    if match:
                        params['normal_morphology'] = float(match.group(1))
                except:
                    pass
        return params
    def _extract_oocyte_parameters(self, llm_analysis: str) -> dict:
        params = {}
        if 'MII' in llm_analysis or 'Metaphase II' in llm_analysis:
            params['maturity'] = OocyteMaturity.MII
        elif 'MI' in llm_analysis or 'Metaphase I' in llm_analysis:
            params['maturity'] = OocyteMaturity.MI
        elif 'GV' in llm_analysis or 'Germinal Vesicle' in llm_analysis:
            params['maturity'] = OocyteMaturity.GV
        import re
        score_match = re.search(r'score.*?(\d)', llm_analysis)
        if score_match:
            params['morphology_score'] = int(score_match.group(1))
        return params
    def _extract_embryo_parameters(self, llm_analysis: str, day: int) -> dict:
        params = {}
        import re
        cell_match = re.search(r'(\d+)\s*(?:blastomeres?|cells?)', llm_analysis)
        if cell_match:
            params['cell_count'] = int(cell_match.group(1))
        frag_match = re.search(r'(\d+\.?\d*)\s*%.*fragmentation', llm_analysis)
        if frag_match:
            params['fragmentation'] = float(frag_match.group(1))
        if day >= 5:
            expansion_match = re.search(r'expansion.*?(\d)', llm_analysis)
            if expansion_match:
                params['expansion'] = expansion_match.group(1)
            icm_match = re.search(r'ICM.*?([ABC])', llm_analysis)
            if icm_match:
                params['inner_cell_mass'] = icm_match.group(1)
            te_match = re.search(r'TE.*?([ABC])', llm_analysis)
            if te_match:
                params['trophectoderm'] = te_match.group(1)
        return params
    def _store_image_analysis(self, sample_id: str, analysis_type: str, image_path: str, llm_analysis: str, processed_data: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO image_analyses 
            (sample_id, analysis_type, image_path, llm_analysis, processed_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sample_id, analysis_type, image_path, llm_analysis, json.dumps(processed_data), datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
    def generate_enhanced_report(self, analysis_type: str, analysis_id: str) -> str:
        standard_report = self.generate_report(analysis_type, analysis_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT image_path, llm_analysis FROM image_analyses 
            WHERE sample_id = ? AND analysis_type = ?
        ''', (analysis_id, analysis_type))
        image_result = cursor.fetchone()
        conn.close()
        if image_result:
            image_path, llm_analysis = image_result
            enhanced_report = standard_report + f"""

IMAGE ANALYSIS SECTION
{'='*50}

Image File: {os.path.basename(image_path)}
Analysis Method: DeepSeek LLM Vision Analysis

DETAILED IMAGE ASSESSMENT:
{llm_analysis}

{'='*50}
"""
            return enhanced_report
        else:
            return standard_report
