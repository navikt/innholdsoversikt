#!/usr/bin/env python3
"""
Test script to validate that all required packages can be imported
without errors, especially testing the pandas/numpy compatibility.
"""

def test_core_imports():
    """Test all core dependencies that main.py uses"""
    try:
        # Core data processing libraries
        import pandas as pd
        import numpy as np
        print(f"✓ pandas {pd.__version__}")
        print(f"✓ numpy {np.__version__}")
        
        # Google Cloud libraries
        from google.cloud import bigquery
        from google.cloud import storage
        print("✓ google-cloud-bigquery")
        print("✓ google-cloud-storage")
        
        # Other required libraries
        import requests
        import json
        import os
        import time
        import zipfile
        from dotenv import load_dotenv
        print("✓ All other required libraries")
        
        # Test basic pandas operations that main.py uses
        df = pd.DataFrame({'test': [1, 2, 3]})
        df['date'] = pd.to_datetime('2025-01-01')
        df['normalized_date'] = df['date'].dt.date
        assert len(df) == 3
        print("✓ Core pandas operations work")
        
        print("\n🎉 All dependencies import successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error importing dependencies: {e}")
        return False

if __name__ == "__main__":
    test_core_imports()
