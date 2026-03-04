from scholare.config import load_config
from scholare.pipeline import run_pipeline

# 1. We define our configuration dictionary manually just like the JSON file
my_analysis_config = {
    "query": "federated learning AND differential privacy",
    "limit": 5, 
    "output_dir": "./output_test_programmatic",
    "categories": {
        "Privacy": ["differential", "dp", "epsilon"],
        "Architecture": ["edge", "cloud", "blockchain"]
    },
    "default_category": "Other",
    "download_pdfs": False,
    "sources": ["openalex", "arxiv"]
}

print("\n🚀 Starting Scholare programmatically...")

try:
    # 2. We load it into the Scholare data object
    config_obj = load_config(my_analysis_config)
    
    # 3. We run the pipeline
    run_pipeline(config_obj)
    print("\n✅ Programmatic test completed successfully!")
except Exception as e:
    print(f"\n❌ Error running programmatic test: {e}")
