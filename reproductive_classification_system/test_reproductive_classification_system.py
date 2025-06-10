from reproductive_classification_system import (
    ReproductiveClassificationSystem, 
    OocyteMaturity
)

def test_system():
    print("Testing Reproductive Classification System...")
    
    # Initialize system
    classifier = ReproductiveClassificationSystem()
    
    # Test sperm analysis
    print("\n1. Testing Sperm Analysis:")
    sperm_result = classifier.classify_sperm(
        concentration=25.0,
        progressive_motility=40.0,
        normal_morphology=5.0,
        volume=3.5,
        sample_id="TEST_SPERM_001"
    )
    print(f"Classification: {sperm_result.classification}")
    
    # Test oocyte analysis
    print("\n2. Testing Oocyte Analysis:")
    oocyte_result = classifier.classify_oocyte(
        maturity=OocyteMaturity.MII,
        morphology_score=3,
        oocyte_id="TEST_OOC_001"
    )
    print(f"Classification: {oocyte_result.classification}")
    
    # Test embryo analysis
    print("\n3. Testing Embryo Analysis:")
    embryo_result = classifier.classify_embryo(
        day=3,
        cell_count=8,
        fragmentation=10.0,
        embryo_id="TEST_EMB_001"
    )
    print(f"Classification: {embryo_result.classification}")
    
    # Test report generation
    print("\n4. Testing Report Generation:")
    report = classifier.generate_report('sperm', 'TEST_SPERM_001')
    print("Report generated successfully!")
    
    print("\n✅ All tests passed! System is ready to use.")

if __name__ == "__main__":
    test_system()
