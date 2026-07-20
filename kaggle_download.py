#!/usr/bin/env python3
"""
Kaggle Dataset Downloader for Indian AQI Health Risk 2019-2024
Attempts to download using kaggle-api or provides manual download instructions
"""

import subprocess
import os
import sys

print("\n" + "="*80)
print("KAGGLE DATASET DOWNLOADER")
print("="*80)
print("\nTarget: Indian AQI Trends and Health Risk 2019-2024")
print("URL: https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024\n")

# Check if kaggle CLI is installed
try:
    result = subprocess.run(["kaggle", "--version"], capture_output=True, text=True)
    print(f"✓ Kaggle CLI found: {result.stdout.strip()}")
    
    # Attempt download
    print("\nAttempting to download dataset...")
    print("Dataset: divsmahesh/indian-aqi-trends-and-health-risk-20192024\n")
    
    subprocess.run([
        "kaggle", "datasets", "download", 
        "-d", "divsmahesh/indian-aqi-trends-and-health-risk-20192024",
        "--unzip"
    ], check=True)
    
    print("\n✓ Dataset downloaded successfully!")
    
except FileNotFoundError:
    print("✗ Kaggle CLI not found\n")
    print("INSTALL KAGGLE CLI:")
    print("  pip install kaggle\n")
    
    print("CONFIGURE KAGGLE:")
    print("  1. Go to https://www.kaggle.com/account")
    print("  2. Scroll to 'API' section")
    print("  3. Click 'Create New API Token'")
    print("  4. This downloads kaggle.json")
    print("  5. Save kaggle.json to ~/.kaggle/\n")
    
    print("AFTER SETUP:")
    print("  Run this script again: python3 kaggle_download.py\n")
    
    print("OR MANUAL DOWNLOAD:")
    print("  1. Visit: https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024")
    print("  2. Click 'Download'")
    print("  3. Extract ZIP file to current directory")
    print("  4. Run audit: python3 kaggle_dataset_audit.py\n")
    
except subprocess.CalledProcessError as e:
    print(f"✗ Download failed: {str(e)}\n")
    print("MANUAL DOWNLOAD:")
    print("  1. Visit: https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024")
    print("  2. Click 'Download'")
    print("  3. Extract ZIP file to: C:\\Users\\Kandra Karthik\\Downloads\\VG")
    print("  4. Run audit: python3 kaggle_dataset_audit.py\n")
    
except Exception as e:
    print(f"✗ Error: {str(e)}\n")
    print("Please download manually from:")
    print("  https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024\n")

print("="*80 + "\n")
