# Medical Knowledge Base and Data Sources

## Overview
HelpScopeAI uses a rule-based expert system approach based on established medical guidelines and clinical standards. No machine learning training data is used.

## Clinical Reference Standards

### Biomarker Reference Ranges

#### Diabetes & Glucose Metabolism
- **American Diabetes Association (ADA) Guidelines**
  - Glucose: 70-100 mg/dL (fasting)
  - HbA1c: <5.7% (normal), 5.7-6.4% (prediabetes), ≥6.5% (diabetes)
  - Source: https://diabetes.org/diabetes/a1c/diagnosis

#### Cardiovascular Health
- **American Heart Association (AHA) Cholesterol Guidelines**
  - Total Cholesterol: <200 mg/dL (desirable)
  - LDL: <100 mg/dL (optimal)
  - HDL: >40 mg/dL (men), >50 mg/dL (women)
  - Source: https://www.heart.org/en/health-topics/cholesterol

#### Blood Pressure Standards
- **American College of Cardiology/AHA Guidelines**
  - Normal: <120/80 mmHg
  - Stage 1 Hypertension: 130-139/80-89 mmHg
  - Stage 2 Hypertension: ≥140/90 mmHg
  - Source: https://www.acc.org/latest-in-cardiology/articles/2017/11/08/11/47/mon-5pm-bp-guideline-aha-2017

#### Hematology
- **WHO Anemia Criteria**
  - Hemoglobin: >12 g/dL (women), >13 g/dL (men)
  - Hematocrit: 36-50%
  - Source: https://www.who.int/health-topics/anaemia

#### Thyroid Function
- **American Thyroid Association Guidelines**
  - TSH: 0.4-4.0 mIU/L (normal range)
  - Source: https://www.thyroid.org/thyroid-function-tests/

#### Vitamin Levels
- **National Institutes of Health (NIH) Guidelines**
  - Vitamin D: 30-100 ng/mL (sufficient)
  - Vitamin B12: 200-900 pg/mL
  - Vitamin C: 0.6-2.0 mg/dL
  - Source: https://ods.od.nih.gov/

#### Kidney Function
- **National Kidney Foundation Guidelines**
  - Creatinine: 0.6-1.3 mg/dL
  - Source: https://www.kidney.org/atoz/content/what-creatinine

## Disease Detection Algorithms

### Clinical Decision Rules
Based on established medical criteria:
- Type 2 Diabetes: ADA diagnostic criteria
- Cardiovascular Risk: Framingham Risk Score principles
- Anemia: WHO classification
- Thyroid Disorders: Endocrine Society guidelines

## Sample Test Data

### Synthetic Health Reports
Located in `sample_files/` directory:
- [health_report.csv](file://e:\H1\sample_files\health_report.csv) - Standard normal ranges
- [high_risk_report.csv](file://e:\H1\sample_files\high_risk_report.csv) - Multiple risk factors
- [optimal_health_report.csv](file://e:\H1\sample_files\optimal_health_report.csv) - Excellent health indicators
- [comprehensive_health_report.csv](file://e:\H1\sample_files\comprehensive_health_report.csv) - Complete biomarker panel

### Data Generation
- No real patient data used
- Synthetic values based on population statistics
- Designed to test various clinical scenarios

## Implementation Notes

### Rule-Based Expert System
- Hard-coded medical knowledge (lines 45-514 in app.py)
- Conditional logic for disease detection
- Evidence-based thresholds and ranges
- No machine learning algorithms used

### Quality Assurance
- Reference ranges validated against multiple medical sources
- Clinical logic reviewed for accuracy
- Test scenarios cover edge cases and normal variations

## Disclaimer
This system is for educational and demonstration purposes only. All medical decisions should be made in consultation with qualified healthcare professionals.

## Last Updated
Generated for HelpScopeAI v2.0 - Rule-based Health Analysis System
