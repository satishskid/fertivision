import json
import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpermMotility(Enum):
    PROGRESSIVE = "progressive"
    NON_PROGRESSIVE = "non_progressive"
    IMMOTILE = "immotile"

class SpermMorphology(Enum):
    NORMAL = "normal"
    ABNORMAL_HEAD = "abnormal_head"
    ABNORMAL_MIDPIECE = "abnormal_midpiece"
    ABNORMAL_TAIL = "abnormal_tail"
    MULTIPLE_DEFECTS = "multiple_defects"

class OocyteMaturity(Enum):
    MII = "metaphase_ii"  # Mature
    MI = "metaphase_i"    # Intermediate
    GV = "germinal_vesicle"  # Immature

class EmbryoGrade(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class SpermAnalysis:
    sample_id: str
    concentration: float  # million/ml
    total_count: float    # million
    progressive_motility: float  # percentage
    total_motility: float       # percentage
    normal_morphology: float    # percentage
    vitality: float            # percentage
    ph: float
    volume: float              # ml
    liquefaction_time: int     # minutes
    classification: str
    notes: str
    timestamp: str

@dataclass
class OocyteAnalysis:
    oocyte_id: str
    maturity: OocyteMaturity
    morphology_score: int  # 1-4 scale
    cumulus_cells: str     # expanded, compact, absent
    zona_pellucida: str    # normal, thick, thin, irregular
    cytoplasm: str         # homogeneous, granular, vacuolated
    polar_body: str        # present, absent, fragmented
    classification: str
    viability: bool
    notes: str
    timestamp: str

@dataclass
class EmbryoAnalysis:
    embryo_id: str
    day: int               # Day of development
    cell_count: int
    fragmentation: float   # percentage
    symmetry: str          # symmetric, asymmetric
    multinucleation: bool
    zona_pellucida: str
    grade: EmbryoGrade
    blastocyst_grade: Optional[str]  # For day 5-6 embryos
    inner_cell_mass: Optional[str]   # A, B, C
    trophectoderm: Optional[str]     # A, B, C
    expansion: Optional[str]         # 1-6 scale for blastocysts
    classification: str
    viability: bool
    transfer_quality: bool
    freeze_quality: bool
    notes: str
    timestamp: str

class ReproductiveClassificationSystem:
    def __init__(self, db_path: str = "reproductive_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing analyses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for each analysis type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sperm_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oocyte_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oocyte_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embryo_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                embryo_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def classify_sperm(self, 
                      concentration: float,
                      progressive_motility: float,
                      normal_morphology: float,
                      **kwargs) -> SpermAnalysis:
        """
        Classify sperm sample according to WHO 2021 criteria
        """
        # WHO 2021 reference values for normozoospermia
        classification_criteria = {
            'concentration': 15,      # million/ml
            'progressive_motility': 32,  # %
            'normal_morphology': 4    # %
        }
        
        # Determine classification based on WHO criteria
        if (concentration >= 15 and 
            progressive_motility >= 32 and 
            normal_morphology >= 4):
            classification = "Normozoospermia"
        else:
            issues = []
            if concentration < 15:
                if concentration < 1:
                    issues.append("Severe oligozoospermia")
                elif concentration < 5:
                    issues.append("Moderate oligozoospermia")
                else:
                    issues.append("Mild oligozoospermia")
            
            if progressive_motility < 32:
                issues.append("Asthenozoospermia")
            
            if normal_morphology < 4:
                issues.append("Teratozoospermia")
            
            classification = " + ".join(issues) if issues else "Atypical"
        
        # Create analysis object with all parameters
        analysis = SpermAnalysis(
            sample_id=kwargs.get('sample_id', f"SPERM_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            concentration=concentration,
            total_count=kwargs.get('total_count', concentration * kwargs.get('volume', 0)),
            progressive_motility=progressive_motility,
            total_motility=kwargs.get('total_motility', progressive_motility + kwargs.get('non_progressive', 0)),
            normal_morphology=normal_morphology,
            vitality=kwargs.get('vitality', 0),
            ph=kwargs.get('ph', 7.2),
            volume=kwargs.get('volume', 0),
            liquefaction_time=kwargs.get('liquefaction_time', 30),
            classification=classification,
            notes=kwargs.get('notes', ''),
            timestamp=datetime.datetime.now().isoformat()
        )
        
        # Store in database
        self._store_analysis('sperm_analyses', analysis.sample_id, analysis)
        
        logger.info(f"Sperm analysis completed: {classification}")
        return analysis
    
    def classify_oocyte(self,
                       maturity: OocyteMaturity,
                       morphology_score: int,
                       **kwargs) -> OocyteAnalysis:
        """
        Classify oocyte according to ESHRE guidelines
        """
        # Determine classification based on maturity and morphology
        if maturity == OocyteMaturity.MII and morphology_score >= 3:
            classification = "Excellent quality - suitable for ICSI"
            viability = True
        elif maturity == OocyteMaturity.MII and morphology_score >= 2:
            classification = "Good quality - suitable for ICSI"
            viability = True
        elif maturity == OocyteMaturity.MII:
            classification = "Fair quality - may be used for ICSI"
            viability = True
        elif maturity == OocyteMaturity.MI:
            classification = "Immature - may mature in culture"
            viability = False
        else:  # GV
            classification = "Immature - not suitable for immediate use"
            viability = False
        
        analysis = OocyteAnalysis(
            oocyte_id=kwargs.get('oocyte_id', f"OOC_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            maturity=maturity,
            morphology_score=morphology_score,
            cumulus_cells=kwargs.get('cumulus_cells', 'expanded'),
            zona_pellucida=kwargs.get('zona_pellucida', 'normal'),
            cytoplasm=kwargs.get('cytoplasm', 'homogeneous'),
            polar_body=kwargs.get('polar_body', 'present'),
            classification=classification,
            viability=viability,
            notes=kwargs.get('notes', ''),
            timestamp=datetime.datetime.now().isoformat()
        )
        
        self._store_analysis('oocyte_analyses', analysis.oocyte_id, analysis)
        
        logger.info(f"Oocyte analysis completed: {classification}")
        return analysis
    
    def classify_embryo(self,
                       day: int,
                       cell_count: int,
                       fragmentation: float,
                       **kwargs) -> EmbryoAnalysis:
        """
        Classify embryo according to ASRM/ESHRE guidelines
        """
        # Day-specific classification
        if day <= 3:
            # Cleavage stage embryo classification
            grade, classification = self._classify_cleavage_embryo(day, cell_count, fragmentation, kwargs)
        else:
            # Blastocyst stage embryo classification
            grade, classification = self._classify_blastocyst(kwargs)
        
        # Determine transfer and freeze quality based on grade
        transfer_quality = grade in [EmbryoGrade.EXCELLENT, EmbryoGrade.GOOD]
        freeze_quality = grade in [EmbryoGrade.EXCELLENT, EmbryoGrade.GOOD, EmbryoGrade.FAIR]
        
        analysis = EmbryoAnalysis(
            embryo_id=kwargs.get('embryo_id', f"EMB_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            day=day,
            cell_count=cell_count,
            fragmentation=fragmentation,
            symmetry=kwargs.get('symmetry', 'symmetric'),
            multinucleation=kwargs.get('multinucleation', False),
            zona_pellucida=kwargs.get('zona_pellucida', 'normal'),
            grade=grade,
            blastocyst_grade=kwargs.get('blastocyst_grade'),
            inner_cell_mass=kwargs.get('inner_cell_mass'),
            trophectoderm=kwargs.get('trophectoderm'),
            expansion=kwargs.get('expansion'),
            classification=classification,
            viability=grade != EmbryoGrade.POOR,
            transfer_quality=transfer_quality,
            freeze_quality=freeze_quality,
            notes=kwargs.get('notes', ''),
            timestamp=datetime.datetime.now().isoformat()
        )
        
        self._store_analysis('embryo_analyses', analysis.embryo_id, analysis)
        
        logger.info(f"Embryo analysis completed: {classification}")
        return analysis
    
    def _classify_cleavage_embryo(self, day: int, cell_count: int, fragmentation: float, kwargs: dict) -> Tuple[EmbryoGrade, str]:
        """Classify cleavage stage embryos (Day 1-3)"""
        expected_cells = {1: 2, 2: 4, 3: 8}
        expected = expected_cells.get(day, 8)
        
        # Grade based on cell number, fragmentation, and symmetry
        if (cell_count >= expected * 0.8 and 
            fragmentation <= 10 and 
            kwargs.get('symmetry') == 'symmetric' and 
            not kwargs.get('multinucleation', False)):
            return EmbryoGrade.EXCELLENT, f"Grade A - Excellent Day {day} embryo"
        elif (cell_count >= expected * 0.6 and 
              fragmentation <= 25 and 
              not kwargs.get('multinucleation', False)):
            return EmbryoGrade.GOOD, f"Grade B - Good Day {day} embryo"
        elif cell_count >= expected * 0.4 and fragmentation <= 50:
            return EmbryoGrade.FAIR, f"Grade C - Fair Day {day} embryo"
        else:
            return EmbryoGrade.POOR, f"Grade D - Poor Day {day} embryo"
    
    def _classify_blastocyst(self, kwargs: dict) -> Tuple[EmbryoGrade, str]:
        """Classify blastocyst stage embryos (Day 5-6) using Gardner grading"""
        expansion = kwargs.get('expansion', '3')
        icm = kwargs.get('inner_cell_mass', 'B')
        te = kwargs.get('trophectoderm', 'B')
        
        # Gardner grading system
        if expansion in ['4', '5', '6'] and icm == 'A' and te == 'A':
            return EmbryoGrade.EXCELLENT, f"Grade {expansion}AA - Excellent blastocyst"
        elif expansion in ['3', '4', '5'] and icm in ['A', 'B'] and te in ['A', 'B']:
            return EmbryoGrade.GOOD, f"Grade {expansion}{icm}{te} - Good blastocyst"
        elif expansion in ['2', '3'] and icm in ['B', 'C'] and te in ['B', 'C']:
            return EmbryoGrade.FAIR, f"Grade {expansion}{icm}{te} - Fair blastocyst"
        else:
            return EmbryoGrade.POOR, f"Grade {expansion}{icm}{te} - Poor blastocyst"
    
    def _store_analysis(self, table: str, id_value: str, analysis):
        """Store analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Determine the correct id field name for the table
        if table == 'sperm_analyses':
            id_field = 'sample_id'
        elif table == 'oocyte_analyses':
            id_field = 'oocyte_id'
        elif table == 'embryo_analyses':
            id_field = 'embryo_id'
        else:
            raise ValueError('Unknown table for storing analysis')

        # Use a custom encoder to handle Enum serialization
        def default_encoder(obj):
            if isinstance(obj, Enum):
                return obj.value
            return str(obj)

        cursor.execute(f'''
            INSERT OR REPLACE INTO {table} (
                {id_field}, data, timestamp
            ) VALUES (?, ?, ?)
        ''', (getattr(analysis, id_field), 
              json.dumps(asdict(analysis), default=default_encoder), 
              analysis.timestamp))
        
        conn.commit()
        conn.close()
    
    def generate_report(self, analysis_type: str, analysis_id: str) -> str:
        """Generate detailed report for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        table_map = {
            'sperm': 'sperm_analyses',
            'oocyte': 'oocyte_analyses', 
            'embryo': 'embryo_analyses'
        }
        
        table = table_map.get(analysis_type)
        if not table:
            return "Invalid analysis type"
        
        # Map analysis_type to correct id field
        id_field_map = {
            'sperm': 'sample_id',
            'oocyte': 'oocyte_id',
            'embryo': 'embryo_id'
        }
        id_field = id_field_map.get(analysis_type)
        if not id_field:
            return "Invalid analysis type"
        cursor.execute(f"SELECT data FROM {table} WHERE {id_field} = ?", (analysis_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return f"No analysis found for ID: {analysis_id}"
        
        data = json.loads(result[0])
        
        # Generate formatted report
        report = f"""
REPRODUCTIVE ANALYSIS REPORT
{'='*50}

Analysis Type: {analysis_type.upper()}
Sample ID: {analysis_id}
Date: {data['timestamp']}

CLASSIFICATION: {data['classification']}

"""
        
        if analysis_type == 'sperm':
            report += f"""
SPERM ANALYSIS PARAMETERS:
- Concentration: {data['concentration']} million/ml
- Progressive Motility: {data['progressive_motility']}%
- Normal Morphology: {data['normal_morphology']}%
- Total Motility: {data['total_motility']}%
- Volume: {data['volume']} ml
- pH: {data['ph']}
- Vitality: {data['vitality']}%

REFERENCE VALUES (WHO 2021):
- Concentration: ≥15 million/ml
- Progressive Motility: ≥32%
- Normal Morphology: ≥4%
"""
        
        elif analysis_type == 'oocyte':
            report += f"""
OOCYTE ANALYSIS PARAMETERS:
- Maturity: {data['maturity']}
- Morphology Score: {data['morphology_score']}/4
- Cumulus Cells: {data['cumulus_cells']}
- Zona Pellucida: {data['zona_pellucida']}
- Cytoplasm: {data['cytoplasm']}
- Polar Body: {data['polar_body']}
- Viability: {'Yes' if data['viability'] else 'No'}
"""
        
        elif analysis_type == 'embryo':
            report += f"""
EMBRYO ANALYSIS PARAMETERS:
- Development Day: {data['day']}
- Cell Count: {data['cell_count']}
- Fragmentation: {data['fragmentation']}%
- Symmetry: {data['symmetry']}
- Multinucleation: {'Yes' if data['multinucleation'] else 'No'}
- Grade: {data['grade']}
- Transfer Quality: {'Yes' if data['transfer_quality'] else 'No'}
- Freeze Quality: {'Yes' if data['freeze_quality'] else 'No'}
"""
            
            if data.get('blastocyst_grade'):
                report += f"""
BLASTOCYST PARAMETERS:
- Expansion: {data['expansion']}
- Inner Cell Mass: {data['inner_cell_mass']}
- Trophectoderm: {data['trophectoderm']}
- Blastocyst Grade: {data['blastocyst_grade']}
"""
        
        if data['notes']:
            report += f"\nNOTES: {data['notes']}\n"
        
        report += f"\n{'='*50}\n"
        
        return report

# Example usage and testing
def main():
    # Initialize the classification system
    classifier = ReproductiveClassificationSystem()
    
    # Example sperm analysis
    sperm_result = classifier.classify_sperm(
        concentration=20.5,
        progressive_motility=45,
        normal_morphology=6,
        volume=3.2,
        total_motility=55,
        vitality=85,
        sample_id="SPERM_001",
        notes="Good quality sample"
    )
    
    # Example oocyte analysis
    oocyte_result = classifier.classify_oocyte(
        maturity=OocyteMaturity.MII,
        morphology_score=4,
        oocyte_id="OOC_001",
        cumulus_cells="expanded",
        notes="Excellent morphology"
    )
    
    # Example embryo analysis
    embryo_result = classifier.classify_embryo(
        day=3,
        cell_count=8,
        fragmentation=5,
        embryo_id="EMB_001",
        symmetry="symmetric",
        multinucleation=False,
        notes="High quality embryo"
    )
    
    # Generate reports
    print(classifier.generate_report('sperm', 'SPERM_001'))
    print(classifier.generate_report('oocyte', 'OOC_001'))
    print(classifier.generate_report('embryo', 'EMB_001'))

if __name__ == "__main__":
    main()
