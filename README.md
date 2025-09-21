# HealthScoreAI

A complete full-stack web application for analyzing health reports and providing AI-powered insights. **Now supports multiple file uploads for collective analysis with enhanced dynamic UI!**

## 🎨 Latest Updates - v2.0

- **🎯 Brand New Identity**: Renamed to "HealthScoreAI" with modern branding
- **💫 Dynamic UI**: Enhanced with modern gradients, animations, and responsive design
- **📊 Smart Biomarker Analysis**: New intelligent insights with optimal range detection
- **🎨 Color-Coded Results**: Visual indicators for optimal, above, and below range values
- **⚡ Real-time Updates**: Dynamic results without page refresh
- **🏷️ Enhanced Status System**: Clear optimal/non-optimal categorization

## 🆕 New Features

- **📁 Multiple File Upload**: Upload several health reports at once
- **🔗 Collective Analysis**: Biomarker values averaged across multiple reports
- **📊 Trend Analysis**: Compare health data over time
- **📋 File Processing Summary**: See details of all processed files
- **✅ Health Status Indicator**: Shows "Everything Fine" when all biomarkers are optimal

## Features

- **File Upload Support**: PDF, Image (JPG/PNG), and CSV files (single or multiple)
- **Comprehensive Biomarker Display**: Shows ALL readings from input files, regardless of optimal status
- **Biomarker Analysis**: Color-coded analysis with precise range messaging:
  - ✅ **Optimal**: "This is within optimal range"
  - 🔵 **Below/Above Optimal**: "This is below/above optimal range; acceptable range is X–Y"
  - ⚠️ **Above Acceptable**: "This is above acceptable range; acceptable range is X–Y" 
  - 🔴 **Below Acceptable**: "This is below acceptable range; acceptable range is X–Y"
- **Disease Detection**: Rule-based detection of potential health conditions
- **Symptom Analysis**: Common symptoms for detected conditions
- **Personalized Recommendations**: Categorized actionable recommendations
- **Collective Insights**: Comprehensive analysis across multiple reports

## Quick Start

### Option 1: Automated Setup (Windows)
```bash
start_server.bat
```

### Option 2: Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Install Tesseract OCR** (for image processing)
```bash
winget install UB-Mannheim.TesseractOCR
```

3. **Run the Application**
```bash
python app.py
```

4. **Open in Browser**
Navigate to: http://localhost:5000

## Testing

Run the comprehensive test suite:
```bash
python test_app.py
```

This will test all file types (CSV, PDF, Images) and verify OCR functionality.

## Sample Files

The `sample_files/` directory contains example health reports:
- `health_report.csv` - Standard health report with normal ranges
- `comprehensive_health_report.csv` - Complete biomarker set (16+ parameters)
- `mixed_optimal_report.csv` - Mix of optimal and non-optimal values
- `high_risk_report.csv` - High-risk patient data (triggers multiple conditions)
- `optimal_health_report.csv` - Excellent health indicators
- `optimal_health_comprehensive.csv` - All biomarkers at optimal levels
- `report_2023.csv` - Historical health data (2023)
- `report_2024.csv` - Recent health data (2024)
- `health_report_image.png` - Sample image for OCR testing
- `health_report.txt` - Text-based health report

**Multiple File Testing**: Upload `report_2023.csv` and `report_2024.csv` together to see collective analysis in action!

## Enhanced Disease Detection

The system now detects **20+ different health conditions**:

**High Risk:**
- Type 2 Diabetes
- Metabolic Syndrome Risk
- Cardiovascular Disease Risk
- Vitamin B12 Deficiency
- Stage 2 Hypertension
- Kidney Dysfunction

**Medium Risk:**
- Prediabetes
- Elevated Blood Glucose
- High Cholesterol
- Moderate Cardiovascular Risk
- Iron Deficiency Anemia
- Hypothyroidism
- Hyperthyroidism
- Vitamin D Deficiency
- Vitamin C Deficiency
- Stage 1 Hypertension
- Low Blood Pressure (Hypotension)
- Tachycardia (Rapid Heart Rate)

**Low Risk:**
- Mild Anemia
- Borderline Hypothyroidism
- Vitamin D Insufficiency
- Bradycardia (Slow Heart Rate)

## Smart Symptom Analysis

The system provides comprehensive symptom analysis based on:
- **Detected diseases** - Specific symptoms for identified conditions
- **Individual biomarkers** - Symptoms based on lab value ranges
- **General health indicators** - Always provides actionable health monitoring advice

## File Structure

- `index.html` - Frontend dashboard with modern UI
- `app.py` - Flask backend with rule-based analysis engine
- `requirements.txt` - Python dependencies
- `start_server.bat` - Automated setup script for Windows
- `test_app.py` - Comprehensive test suite
- `create_sample_image.py` - Generate sample test images

## Supported Biomarkers

### Core Health Markers
- Glucose
- HbA1c
- Total Cholesterol
- LDL Cholesterol
- HDL Cholesterol
- Hemoglobin
- Hematocrit
- TSH (Thyroid Stimulating Hormone)

### Vitamin Levels
- **Vitamin D** (25-hydroxyvitamin D)
- **Vitamin B12** (Cobalamin)
- **Vitamin C** (Ascorbic Acid)
- **Vitamin A** (Retinol)

### Cardiovascular Markers
- **Systolic Blood Pressure**
- **Diastolic Blood Pressure**
- **Heart Rate/Pulse**

### Additional Health Markers
- **Creatinine** (Kidney Function)

## Health Conditions Detected

- Type 2 Diabetes
- Prediabetes
- Cardiovascular Disease Risk
- Iron Deficiency Anemia
- Hypothyroidism
- Hyperthyroidism

## Technology Stack

**Frontend:**
- HTML5 + Tailwind CSS
- Vanilla JavaScript
- Responsive design

**Backend:**
- Python Flask
- PyPDF2 (PDF processing)
- Pillow + Pytesseract (OCR)
- Rule-based analysis engine

## Troubleshooting

### Image Processing Issues
If you encounter issues with image processing:

1. **Install Tesseract OCR:**
   ```bash
   # Windows (using winget)
   winget install UB-Mannheim.TesseractOCR
   
   # Windows (manual)
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   # Install to: C:\Program Files\Tesseract-OCR\
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   ```

2. **Verify Tesseract installation:**
   ```bash
   # Windows
   "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
   
   # Linux/macOS  
   tesseract --version
   ```

3. **Check image quality:**
   - Use high-resolution images (at least 300x300 pixels)
   - Ensure text is clearly readable
   - Use good contrast (dark text on light background)
   - Avoid blurry or skewed images

4. **Alternative formats:**
   - CSV format works best and is most reliable
   - PDF format also works well for text-based documents

### General Issues
If you encounter "code language not supported" error:
1. Ensure Tesseract OCR is properly installed
2. Run `start_server.bat` for automated setup
3. Run `python test_app.py` to verify all components

## Notes

- Maximum file size: 10MB
- All analysis rules are hard-coded for hackathon demo purposes
- Sample data will be used if no biomarkers are detected in uploaded files
- This is for educational/demo purposes only - not for actual medical diagnosis