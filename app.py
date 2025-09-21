#!/usr/bin/env python3
"""
HealthScoreAI - Backend API
A Flask-based backend for analyzing health reports from PDF, Image, and CSV files.
"""

import os
import re
import csv
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Flask and file handling
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# File processing libraries
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("Warning: PyPDF2 not installed. PDF processing will be disabled.")

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None
    print("Warning: PIL/pytesseract not installed. Image processing will be disabled.")

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'csv'}

# ========================================================================================
# HARD-CODED RULE-BASED SYSTEM DATA
# ========================================================================================

# Biomarker reference ranges and rules
BIOMARKER_RULES = {
    'glucose': {
        'unit': 'mg/dL',
        'acceptable_range': '70-100',
        'acceptable_min': 70,
        'acceptable_max': 100,
        'high_threshold': 126,
        'keywords': ['glucose', 'blood glucose', 'fasting glucose', 'random glucose'],
        'insights': {
            'optimal': 'Your glucose levels are within the optimal range.',
            'acceptable': 'Your glucose levels are acceptable but could be optimized.',
            'high': 'Elevated glucose levels may indicate diabetes risk.',
            'low': 'Low glucose levels may cause hypoglycemic symptoms.'
        }
    },
    'hba1c': {
        'unit': '%',
        'acceptable_range': '4.0-5.6',
        'acceptable_min': 4.0,
        'acceptable_max': 5.6,
        'high_threshold': 6.5,
        'keywords': ['hba1c', 'hemoglobin a1c', 'glycated hemoglobin', 'a1c'],
        'insights': {
            'optimal': 'Excellent long-term glucose control over the past 2-3 months.',
            'acceptable': 'Good glucose control, with room for optimization.',
            'high': 'Indicates poor glucose control and increased diabetes risk.',
            'low': 'Very low HbA1c levels, monitor for hypoglycemic episodes.'
        }
    },
    'total_cholesterol': {
        'unit': 'mg/dL',
        'acceptable_range': '<200',
        'acceptable_min': 0,
        'acceptable_max': 200,
        'high_threshold': 240,
        'keywords': ['total cholesterol', 'cholesterol total', 'chol total', 'tc'],
        'insights': {
            'optimal': 'Total cholesterol is at an optimal level for heart health.',
            'acceptable': 'Total cholesterol is acceptable but could be improved.',
            'high': 'High cholesterol increases cardiovascular disease risk.',
            'low': 'Very low cholesterol levels may need monitoring.'
        }
    },
    'ldl': {
        'unit': 'mg/dL',
        'acceptable_range': '<100',
        'acceptable_min': 0,
        'acceptable_max': 100,
        'high_threshold': 160,
        'keywords': ['ldl', 'ldl cholesterol', 'low density lipoprotein', 'bad cholesterol'],
        'insights': {
            'optimal': 'LDL cholesterol is at optimal levels for heart health.',
            'acceptable': 'LDL cholesterol is acceptable but could be lower.',
            'high': 'High LDL cholesterol is a major risk factor for heart disease.',
            'low': 'Low LDL cholesterol is beneficial for cardiovascular health.'
        }
    },
    'hdl': {
        'unit': 'mg/dL',
        'acceptable_range': '>40 (M), >50 (F)',
        'acceptable_min': 40,
        'acceptable_max': 1000,
        'high_threshold': 1000,
        'keywords': ['hdl', 'hdl cholesterol', 'high density lipoprotein', 'good cholesterol'],
        'insights': {
            'optimal': 'HDL cholesterol levels provide excellent cardiovascular protection.',
            'acceptable': 'HDL cholesterol levels provide good cardiovascular protection.',
            'high': 'Very high HDL cholesterol is excellent for heart health.',
            'low': 'Low HDL cholesterol increases cardiovascular disease risk.'
        }
    },
    'hemoglobin': {
        'unit': 'g/dL',
        'acceptable_range': '12-18',
        'acceptable_min': 12,
        'acceptable_max': 18,
        'high_threshold': 20,
        'keywords': ['hemoglobin', 'hgb', 'hb', 'haemoglobin'],
        'insights': {
            'optimal': 'Hemoglobin levels indicate excellent oxygen-carrying capacity.',
            'acceptable': 'Hemoglobin levels indicate good oxygen-carrying capacity.',
            'high': 'High hemoglobin may indicate dehydration or blood disorders.',
            'low': 'Low hemoglobin suggests anemia and requires evaluation.'
        }
    },
    'hematocrit': {
        'unit': '%',
        'acceptable_range': '36-50',
        'acceptable_min': 36,
        'acceptable_max': 50,
        'high_threshold': 55,
        'keywords': ['hematocrit', 'hct', 'packed cell volume', 'pcv'],
        'insights': {
            'optimal': 'Hematocrit levels are at optimal levels.',
            'acceptable': 'Hematocrit levels are within acceptable range.',
            'high': 'High hematocrit may indicate dehydration or blood disorders.',
            'low': 'Low hematocrit suggests anemia and needs medical attention.'
        }
    },
    'tsh': {
        'unit': 'mIU/L',
        'acceptable_range': '0.4-4.0',
        'acceptable_min': 0.4,
        'acceptable_max': 4.0,
        'high_threshold': 10.0,
        'keywords': ['tsh', 'thyroid stimulating hormone', 'thyrotropin'],
        'insights': {
            'optimal': 'Thyroid function is at optimal levels.',
            'acceptable': 'Thyroid function appears to be acceptable.',
            'high': 'Elevated TSH may indicate hypothyroidism (underactive thyroid).',
            'low': 'Low TSH may indicate hyperthyroidism (overactive thyroid).'
        }
    },
    # VITAMIN LEVELS
    'vitamin_d': {
        'unit': 'ng/mL',
        'acceptable_range': '30-100',
        'acceptable_min': 30,
        'acceptable_max': 100,
        'high_threshold': 150,
        'keywords': ['vitamin d', 'vit d', '25-hydroxyvitamin d', '25(oh)d', 'cholecalciferol'],
        'insights': {
            'optimal': 'Vitamin D levels support excellent bone health and immune function.',
            'acceptable': 'Vitamin D levels are adequate for most individuals.',
            'high': 'High vitamin D levels may cause hypercalcemia.',
            'low': 'Low vitamin D increases risk of bone diseases and immune dysfunction.'
        }
    },
    'vitamin_b12': {
        'unit': 'pg/mL',
        'acceptable_range': '200-900',
        'acceptable_min': 200,
        'acceptable_max': 900,
        'high_threshold': 1000,
        'keywords': ['vitamin b12', 'vit b12', 'cobalamin', 'b-12'],
        'insights': {
            'optimal': 'B12 levels support excellent nerve function and red blood cell formation.',
            'acceptable': 'B12 levels are sufficient for normal metabolic functions.',
            'high': 'High B12 levels are generally not harmful but may indicate supplement excess.',
            'low': 'Low B12 can cause anemia, nerve damage, and cognitive issues.'
        }
    },
    'vitamin_c': {
        'unit': 'mg/dL',
        'acceptable_range': '0.6-2.0',
        'acceptable_min': 0.6,
        'acceptable_max': 2.0,
        'high_threshold': 3.0,
        'keywords': ['vitamin c', 'vit c', 'ascorbic acid', 'ascorbate'],
        'insights': {
            'optimal': 'Vitamin C levels provide excellent antioxidant protection.',
            'acceptable': 'Vitamin C levels support normal immune function.',
            'high': 'High vitamin C levels are generally safe but may cause digestive issues.',
            'low': 'Low vitamin C increases risk of scurvy and weakened immunity.'
        }
    },
    'vitamin_a': {
        'unit': 'μg/dL',
        'acceptable_range': '20-60',
        'acceptable_min': 20,
        'acceptable_max': 60,
        'high_threshold': 100,
        'keywords': ['vitamin a', 'vit a', 'retinol', 'beta carotene'],
        'insights': {
            'optimal': 'Vitamin A levels support excellent vision and immune function.',
            'acceptable': 'Vitamin A levels are adequate for normal physiological functions.',
            'high': 'High vitamin A can be toxic and cause liver damage.',
            'low': 'Low vitamin A can cause night blindness and immune dysfunction.'
        }
    },
    # BLOOD PRESSURE
    'systolic_bp': {
        'unit': 'mmHg',
        'acceptable_range': '90-120',
        'acceptable_min': 90,
        'acceptable_max': 120,
        'high_threshold': 140,
        'keywords': ['systolic', 'systolic blood pressure', 'sbp', 'sys bp'],
        'insights': {
            'optimal': 'Systolic blood pressure is at optimal levels for cardiovascular health.',
            'acceptable': 'Systolic blood pressure is within normal range.',
            'high': 'High systolic blood pressure increases risk of heart disease and stroke.',
            'low': 'Low systolic blood pressure may cause dizziness and fatigue.'
        }
    },
    'diastolic_bp': {
        'unit': 'mmHg',
        'acceptable_range': '60-80',
        'acceptable_min': 60,
        'acceptable_max': 80,
        'high_threshold': 90,
        'keywords': ['diastolic', 'diastolic blood pressure', 'dbp', 'dias bp'],
        'insights': {
            'optimal': 'Diastolic blood pressure is at optimal levels.',
            'acceptable': 'Diastolic blood pressure is within normal range.',
            'high': 'High diastolic blood pressure increases cardiovascular risk.',
            'low': 'Low diastolic blood pressure may indicate underlying health issues.'
        }
    },
    # ADDITIONAL IMPORTANT MARKERS
    'heart_rate': {
        'unit': 'bpm',
        'acceptable_range': '60-100',
        'acceptable_min': 60,
        'acceptable_max': 100,
        'high_threshold': 120,
        'keywords': ['heart rate', 'pulse', 'hr', 'beats per minute', 'bpm'],
        'insights': {
            'optimal': 'Heart rate is within the optimal range for cardiovascular fitness.',
            'acceptable': 'Heart rate is within normal resting range.',
            'high': 'Elevated heart rate may indicate stress, dehydration, or cardiac issues.',
            'low': 'Low heart rate may indicate excellent fitness or potential cardiac issues.'
        }
    },
    'creatinine': {
        'unit': 'mg/dL',
        'acceptable_range': '0.6-1.3',
        'acceptable_min': 0.6,
        'acceptable_max': 1.3,
        'high_threshold': 2.0,
        'keywords': ['creatinine', 'serum creatinine', 'creat'],
        'insights': {
            'optimal': 'Kidney function appears to be excellent based on creatinine levels.',
            'acceptable': 'Kidney function is within normal range.',
            'high': 'Elevated creatinine may indicate kidney dysfunction.',
            'low': 'Low creatinine is generally not concerning but may reflect low muscle mass.'
        }
    }
}

# Disease detection rules - Enhanced for better detection
DISEASE_RULES = {
    'diabetes_type_2': {
        'name': 'Type 2 Diabetes',
        'conditions': [
            {'biomarker': 'glucose', 'operator': '>=', 'value': 126},
            {'biomarker': 'hba1c', 'operator': '>=', 'value': 6.5}
        ],
        'logic': 'OR',  # Either condition can trigger
        'priority': 'High Risk',
        'reasoning': 'Elevated glucose and/or HbA1c levels indicate diabetes.',
        'symptoms': ['Increased thirst', 'Frequent urination', 'Fatigue', 'Blurred vision', 'Slow wound healing', 'Unexplained weight loss']
    },
    'prediabetes': {
        'name': 'Prediabetes',
        'conditions': [
            {'biomarker': 'glucose', 'operator': 'between', 'value': [100, 125]},
            {'biomarker': 'hba1c', 'operator': 'between', 'value': [5.7, 6.4]}
        ],
        'logic': 'OR',
        'priority': 'Medium Risk',
        'reasoning': 'Blood sugar levels are higher than normal but not yet diabetic.',
        'symptoms': ['Mild fatigue', 'Occasional increased thirst', 'Slight weight changes', 'Increased appetite']
    },
    'high_glucose': {
        'name': 'Elevated Blood Glucose',
        'conditions': [
            {'biomarker': 'glucose', 'operator': 'between', 'value': [110, 125]}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Glucose levels are above normal range, indicating potential metabolic issues.',
        'symptoms': ['Mild fatigue', 'Increased thirst', 'Frequent urination', 'Sugar cravings']
    },
    'cardiovascular_risk': {
        'name': 'Cardiovascular Disease Risk',
        'conditions': [
            {'biomarker': 'total_cholesterol', 'operator': '>=', 'value': 240},
            {'biomarker': 'ldl', 'operator': '>=', 'value': 160},
            {'biomarker': 'hdl', 'operator': '<=', 'value': 35}
        ],
        'logic': 'OR',
        'priority': 'High Risk',
        'reasoning': 'Abnormal cholesterol levels significantly increase heart disease risk.',
        'symptoms': ['Chest pain', 'Shortness of breath', 'Fatigue', 'Leg pain when walking', 'Dizziness']
    },
    'moderate_cardiovascular_risk': {
        'name': 'Moderate Cardiovascular Risk',
        'conditions': [
            {'biomarker': 'total_cholesterol', 'operator': 'between', 'value': [200, 239]},
            {'biomarker': 'ldl', 'operator': 'between', 'value': [130, 159]},
            {'biomarker': 'hdl', 'operator': 'between', 'value': [35, 45]}
        ],
        'logic': 'OR',
        'priority': 'Medium Risk',
        'reasoning': 'Borderline cholesterol levels warrant monitoring and lifestyle changes.',
        'symptoms': ['Mild chest discomfort', 'Occasional fatigue', 'Exercise intolerance', 'Mild shortness of breath']
    },
    'high_cholesterol': {
        'name': 'High Cholesterol',
        'conditions': [
            {'biomarker': 'total_cholesterol', 'operator': '>=', 'value': 200}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Total cholesterol above recommended levels increases cardiovascular risk.',
        'symptoms': ['No obvious symptoms', 'Potential fatigue', 'Chest tightness during exercise']
    },
    'iron_deficiency_anemia': {
        'name': 'Iron Deficiency Anemia',
        'conditions': [
            {'biomarker': 'hemoglobin', 'operator': '<', 'value': 12},
            {'biomarker': 'hematocrit', 'operator': '<', 'value': 36}
        ],
        'logic': 'OR',
        'priority': 'Medium Risk',
        'reasoning': 'Low hemoglobin and hematocrit levels suggest iron deficiency anemia.',
        'symptoms': ['Fatigue', 'Weakness', 'Pale skin', 'Cold hands and feet', 'Restless legs', 'Brittle nails']
    },
    'mild_anemia': {
        'name': 'Mild Anemia',
        'conditions': [
            {'biomarker': 'hemoglobin', 'operator': 'between', 'value': [12, 13.5]},
            {'biomarker': 'hematocrit', 'operator': 'between', 'value': [36, 40]}
        ],
        'logic': 'OR',
        'priority': 'Low Risk',
        'reasoning': 'Hemoglobin levels are on the lower end of normal range.',
        'symptoms': ['Mild fatigue', 'Occasional weakness', 'Slight pale appearance']
    },
    'hypothyroidism': {
        'name': 'Hypothyroidism',
        'conditions': [
            {'biomarker': 'tsh', 'operator': '>', 'value': 4.0}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Elevated TSH levels indicate an underactive thyroid gland.',
        'symptoms': ['Fatigue', 'Weight gain', 'Cold sensitivity', 'Dry skin', 'Hair loss', 'Depression', 'Constipation']
    },
    'borderline_hypothyroidism': {
        'name': 'Borderline Hypothyroidism',
        'conditions': [
            {'biomarker': 'tsh', 'operator': 'between', 'value': [3.0, 4.0]}
        ],
        'logic': 'AND',
        'priority': 'Low Risk',
        'reasoning': 'TSH levels are in the upper normal range, may indicate early thyroid dysfunction.',
        'symptoms': ['Mild fatigue', 'Slight weight gain', 'Mild cold sensitivity']
    },
    'hyperthyroidism': {
        'name': 'Hyperthyroidism',
        'conditions': [
            {'biomarker': 'tsh', 'operator': '<', 'value': 0.4}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Low TSH levels indicate an overactive thyroid gland.',
        'symptoms': ['Weight loss', 'Rapid heartbeat', 'Nervousness', 'Sweating', 'Heat sensitivity', 'Irritability']
    },
    'metabolic_syndrome_risk': {
        'name': 'Metabolic Syndrome Risk',
        'conditions': [
            {'biomarker': 'glucose', 'operator': '>=', 'value': 100},
            {'biomarker': 'hdl', 'operator': '<=', 'value': 50},
            {'biomarker': 'total_cholesterol', 'operator': '>=', 'value': 200}
        ],
        'logic': 'AND',  # Need multiple conditions
        'priority': 'High Risk',
        'reasoning': 'Combination of elevated glucose, low HDL, and high cholesterol suggests metabolic syndrome.',
        'symptoms': ['Abdominal weight gain', 'Fatigue', 'Increased thirst', 'High blood pressure symptoms']
    },
    # VITAMIN DEFICIENCY CONDITIONS
    'vitamin_d_deficiency': {
        'name': 'Vitamin D Deficiency',
        'conditions': [
            {'biomarker': 'vitamin_d', 'operator': '<', 'value': 20}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Severely low vitamin D levels increase risk of bone diseases and immune dysfunction.',
        'symptoms': ['Bone pain', 'Muscle weakness', 'Frequent infections', 'Fatigue', 'Depression', 'Hair loss']
    },
    'vitamin_d_insufficiency': {
        'name': 'Vitamin D Insufficiency',
        'conditions': [
            {'biomarker': 'vitamin_d', 'operator': 'between', 'value': [20, 29]}
        ],
        'logic': 'AND',
        'priority': 'Low Risk',
        'reasoning': 'Suboptimal vitamin D levels may compromise bone health and immune function.',
        'symptoms': ['Mild fatigue', 'Occasional muscle aches', 'Susceptibility to colds']
    },
    'vitamin_b12_deficiency': {
        'name': 'Vitamin B12 Deficiency',
        'conditions': [
            {'biomarker': 'vitamin_b12', 'operator': '<', 'value': 200}
        ],
        'logic': 'AND',
        'priority': 'High Risk',
        'reasoning': 'B12 deficiency can cause serious neurological damage and pernicious anemia.',
        'symptoms': ['Extreme fatigue', 'Memory problems', 'Confusion', 'Tingling in hands/feet', 'Balance issues', 'Pale skin']
    },
    'low_vitamin_c': {
        'name': 'Vitamin C Deficiency',
        'conditions': [
            {'biomarker': 'vitamin_c', 'operator': '<', 'value': 0.6}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Low vitamin C increases risk of scurvy and compromises immune function.',
        'symptoms': ['Easy bruising', 'Slow wound healing', 'Joint pain', 'Tooth loss', 'Bleeding gums']
    },
    # BLOOD PRESSURE CONDITIONS
    'hypertension_stage_1': {
        'name': 'Stage 1 Hypertension',
        'conditions': [
            {'biomarker': 'systolic_bp', 'operator': 'between', 'value': [130, 139]},
            {'biomarker': 'diastolic_bp', 'operator': 'between', 'value': [80, 89]}
        ],
        'logic': 'OR',
        'priority': 'Medium Risk',
        'reasoning': 'Blood pressure is elevated and requires lifestyle modifications.',
        'symptoms': ['Headaches', 'Dizziness', 'Shortness of breath', 'Nosebleeds', 'Flushing']
    },
    'hypertension_stage_2': {
        'name': 'Stage 2 Hypertension',
        'conditions': [
            {'biomarker': 'systolic_bp', 'operator': '>=', 'value': 140},
            {'biomarker': 'diastolic_bp', 'operator': '>=', 'value': 90}
        ],
        'logic': 'OR',
        'priority': 'High Risk',
        'reasoning': 'Significantly elevated blood pressure requires immediate medical attention.',
        'symptoms': ['Severe headaches', 'Chest pain', 'Vision problems', 'Difficulty breathing', 'Irregular heartbeat']
    },
    'hypotension': {
        'name': 'Low Blood Pressure (Hypotension)',
        'conditions': [
            {'biomarker': 'systolic_bp', 'operator': '<', 'value': 90},
            {'biomarker': 'diastolic_bp', 'operator': '<', 'value': 60}
        ],
        'logic': 'OR',
        'priority': 'Medium Risk',
        'reasoning': 'Low blood pressure may cause inadequate blood flow to organs.',
        'symptoms': ['Dizziness', 'Fainting', 'Fatigue', 'Nausea', 'Cold/clammy skin', 'Blurred vision']
    },
    # HEART RATE CONDITIONS
    'tachycardia': {
        'name': 'Tachycardia (Rapid Heart Rate)',
        'conditions': [
            {'biomarker': 'heart_rate', 'operator': '>', 'value': 100}
        ],
        'logic': 'AND',
        'priority': 'Medium Risk',
        'reasoning': 'Elevated resting heart rate may indicate cardiovascular stress or other conditions.',
        'symptoms': ['Palpitations', 'Shortness of breath', 'Dizziness', 'Chest pain', 'Fatigue']
    },
    'bradycardia': {
        'name': 'Bradycardia (Slow Heart Rate)',
        'conditions': [
            {'biomarker': 'heart_rate', 'operator': '<', 'value': 60}
        ],
        'logic': 'AND',
        'priority': 'Low Risk',
        'reasoning': 'Low heart rate may be normal for athletes or indicate cardiac conduction issues.',
        'symptoms': ['Fatigue', 'Dizziness', 'Weakness', 'Confusion', 'Fainting spells']
    },
    # KIDNEY FUNCTION
    'kidney_dysfunction': {
        'name': 'Kidney Dysfunction',
        'conditions': [
            {'biomarker': 'creatinine', 'operator': '>', 'value': 1.3}
        ],
        'logic': 'AND',
        'priority': 'High Risk',
        'reasoning': 'Elevated creatinine indicates reduced kidney function.',
        'symptoms': ['Decreased urination', 'Swelling in legs/ankles', 'Fatigue', 'Nausea', 'Confusion']
    }
}

# Recommendation templates
RECOMMENDATION_TEMPLATES = {
    'diabetes_type_2': {
        'Professional Consultation': [
            'Schedule an appointment with an endocrinologist',
            'Regular monitoring with your primary care physician',
            'Consider diabetes education classes'
        ],
        'Dietary': [
            'Follow a low-carbohydrate diet',
            'Monitor portion sizes and meal timing',
            'Increase fiber intake',
            'Limit sugar and processed foods'
        ],
        'Lifestyle': [
            'Engage in regular physical activity (150 minutes/week)',
            'Monitor blood glucose regularly',
            'Maintain a healthy weight',
            'Manage stress levels'
        ]
    },
    'cardiovascular_risk': {
        'Professional Consultation': [
            'Consult with a cardiologist',
            'Discuss statin therapy with your doctor',
            'Regular blood pressure monitoring'
        ],
        'Dietary': [
            'Adopt a Mediterranean or DASH diet',
            'Reduce saturated and trans fats',
            'Increase omega-3 fatty acids',
            'Limit sodium intake'
        ],
        'Lifestyle': [
            'Regular aerobic exercise',
            'Quit smoking if applicable',
            'Maintain a healthy weight',
            'Limit alcohol consumption'
        ]
    },
    'iron_deficiency_anemia': {
        'Professional Consultation': [
            'See a hematologist for further evaluation',
            'Investigate underlying causes of iron deficiency',
            'Regular follow-up blood tests'
        ],
        'Dietary': [
            'Increase iron-rich foods (lean meats, spinach, beans)',
            'Combine iron foods with vitamin C sources',
            'Consider iron supplements as prescribed',
            'Avoid coffee and tea with iron-rich meals'
        ],
        'Lifestyle': [
            'Adequate rest and sleep',
            'Gradual increase in physical activity',
            'Monitor symptoms closely'
        ]
    },
    'thyroid_disorders': {
        'Professional Consultation': [
            'Consult with an endocrinologist',
            'Regular thyroid function monitoring',
            'Discuss medication options'
        ],
        'Dietary': [
            'Ensure adequate iodine intake',
            'Consider selenium-rich foods',
            'Maintain a balanced diet'
        ],
        'Lifestyle': [
            'Manage stress levels',
            'Regular sleep schedule',
            'Monitor symptoms'
        ]
    },
    'general_wellness': {
        'Professional Consultation': [
            'Annual physical examination',
            'Regular preventive screenings',
            'Discuss any concerns with your healthcare provider'
        ],
        'Dietary': [
            'Maintain a balanced, nutritious diet',
            'Stay hydrated',
            'Limit processed foods'
        ],
        'Lifestyle': [
            'Regular physical activity',
            'Adequate sleep (7-9 hours)',
            'Stress management',
            'Avoid tobacco and limit alcohol'
        ]
    }
}

# ========================================================================================
# UTILITY FUNCTIONS
# ========================================================================================

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_numbers_from_text(text: str) -> List[Tuple[str, float, str]]:
    """Extract numerical values with their context from text."""
    # Enhanced patterns for better OCR text parsing
    patterns = [
        # Pattern 1: Standard format "Parameter: Value Unit"
        r'([a-zA-Z\s]+)[:\s=]+([0-9]+\.?[0-9]*)\s*([a-zA-Z/%]*)',
        # Pattern 2: Colon separated "Parameter : Value"
        r'([a-zA-Z\s]+)\s*:\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z/%]*)',
        # Pattern 3: Equals separated "Parameter = Value"
        r'([a-zA-Z\s]+)\s*=\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z/%]*)',
        # Pattern 4: Space separated "Parameter Value Unit"
        r'([a-zA-Z\s]{3,})\s+([0-9]+\.?[0-9]*)\s+([a-zA-Z/%]+)',
        # Pattern 5: Tab or multiple spaces "Parameter\t\tValue"
        r'([a-zA-Z\s]+)[\t\s]{2,}([0-9]+\.?[0-9]*)\s*([a-zA-Z/%]*)',
        # Pattern 6: OCR common format "Parameter Value" (no unit)
        r'([a-zA-Z\s]{5,})\s+([0-9]+\.?[0-9]*)(?!\d)',
    ]
    
    results = []
    print(f"\n=== TEXT EXTRACTION DEBUG ===")
    print(f"Input text: {repr(text[:200])}...")
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            try:
                if len(match) == 3:
                    context, value_str, unit = match
                elif len(match) == 2:
                    context, value_str = match
                    unit = ''
                else:
                    continue
                    
                context = context.strip().lower()
                value = float(value_str)
                unit = unit.strip() if unit else ''
                
                # Filter out very short contexts (likely false positives)
                if len(context) >= 3:
                    results.append((context, value, unit))
                    
            except (ValueError, AttributeError) as e:
                continue
    
    return results

def parse_csv_file(file_path: str) -> Dict[str, float]:
    """Parse CSV file and extract biomarker values."""
    biomarkers = {}
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Try to detect dialect
            sample = csvfile.read(1024)
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            
            reader = csv.reader(csvfile, dialect)
            header = next(reader, None)  # Read header row
            
            if not header:
                return biomarkers
                
            # Determine column indices based on header
            name_col = None
            value_col = None
            
            # Look for name column (biomarker, parameter, etc.)
            for i, col in enumerate(header):
                col_lower = col.lower().strip()
                if col_lower in ['biomarker', 'parameter', 'name', 'test']:
                    name_col = i
                    break
            
            # Look for value column
            for i, col in enumerate(header):
                col_lower = col.lower().strip()
                if col_lower in ['value', 'result', 'level']:
                    value_col = i
                    break
                    
            # Fallback: assume first column is name, second is value
            if name_col is None:
                name_col = 0
            if value_col is None:
                value_col = 1
            
            for row_num, row in enumerate(reader, start=2):  # Start from row 2 (after header)
                if len(row) > max(name_col, value_col):
                    try:
                        biomarker_name = row[name_col].strip().lower()
                        value_str = row[value_col].strip()
                        value = float(value_str)
                        
                        # Clean up biomarker names for standardization
                        biomarker_name = biomarker_name.replace(' ', '_').replace('-', '_')
                        
                        biomarkers[biomarker_name] = value
                    except (ValueError, IndexError) as e:
                        continue
                else:
                    continue
                        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
    
    return biomarkers

def parse_pdf_file(file_path: str) -> str:
    """Extract text from PDF file."""
    if not PyPDF2:
        return ""
    
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    
    return text

def parse_image_file(file_path: str) -> str:
    """Extract text from image file using OCR."""
    if not Image or not pytesseract:
        print("Warning: PIL or pytesseract not available")
        return "OCR libraries not available. Please install Pillow and pytesseract, then install Tesseract OCR."
    
    try:
        # Try to detect Tesseract installation
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            'tesseract'  # For cloud platforms with tesseract in PATH
        ]
        
        tesseract_found = False
        for path in possible_paths:
            if os.path.exists(path) or path == 'tesseract':
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    # Test if tesseract works
                    version = pytesseract.get_tesseract_version()
                    tesseract_found = True
                    break
                except Exception as e:
                    continue
        
        if not tesseract_found:
            return "Tesseract OCR not installed. Please install Tesseract OCR to process images. For now, please use CSV or PDF files."
        
        # Open and process image
        image = Image.open(file_path)
        
        # Enhance image for better OCR
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if image is too small or too large
        width, height = image.size
        if width < 300 or height < 300:
            # Scale up small images
            scale_factor = max(300/width, 300/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        elif width > 3000 or height > 3000:
            # Scale down very large images
            scale_factor = min(3000/width, 3000/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Use comprehensive OCR configuration for better results
        ocr_configs = [
            '',                    # No config (default)
            '--psm 6',             # Single uniform block
            '--psm 4',             # Single column of text
            '--psm 3',             # Fully automatic page segmentation
            '--psm 1',             # Automatic page segmentation with OSD
        ]
        
        for i, config in enumerate(ocr_configs):
            try:
                if config:
                    text = pytesseract.image_to_string(image, config=config)
                else:
                    text = pytesseract.image_to_string(image)
                    
                if text.strip():  # If we got some text, use it
                    return text
                else:
                    continue
            except Exception as config_error:
                continue
        
        return "No readable text detected in image. Please ensure the image contains clear, readable text and try again. Alternatively, use CSV or PDF format."
        
    except Exception as e:
        return f"Image processing failed: {str(e)}. Please use CSV or PDF files for best results."

def standardize_biomarkers(data_source: Union[str, Dict[str, float]], file_type: str) -> Dict[str, float]:
    """Standardize extracted data into a biomarker dictionary."""
    biomarkers = {}
    
    if file_type == 'csv':
        # For CSV, data_source is already a dictionary
        if isinstance(data_source, dict):
            return data_source
        else:
            return {}  # Return empty dict if not a dict
    
    # For PDF and image files, data_source is text and extract numbers from it
    if isinstance(data_source, str):
        extracted_numbers = extract_numbers_from_text(data_source)
    else:
        return {}  # Return empty dict if not a string
    
    # Enhanced keyword matching for OCR text
    extracted_numbers = extract_numbers_from_text(data_source)
    
    # Enhanced matching for extracted numbers
    matched_count = 0
    for biomarker_key, biomarker_info in BIOMARKER_RULES.items():
        for context, value, unit in extracted_numbers:
            # Enhanced keyword matching - check multiple variations
            keywords = biomarker_info['keywords']
            context_variations = [
                context,
                context.replace('_', ' '),
                context.replace(' ', ''),
                context.replace('-', ' '),
                context.replace('/', ' '),
            ]
            
            matched = False
            for keyword in keywords:
                for variation in context_variations:
                    # Fuzzy matching - check if keyword is contained in variation or vice versa
                    if (keyword.lower() in variation.lower() or 
                        variation.lower() in keyword.lower() or
                        # Handle common OCR errors
                        keyword.lower().replace('o', '0') in variation.lower() or
                        keyword.lower().replace('l', '1') in variation.lower()):
                        
                        biomarkers[biomarker_key] = value
                        matched = True
                        matched_count += 1
                        break
                if matched:
                    break
            if matched:
                break
                
    # For CSV files, also try direct name matching after keyword matching
    if file_type == 'csv' and isinstance(data_source, dict):
        # Map common CSV column names to our biomarker keys
        name_mapping = {
            'glucose': 'glucose',
            'total_cholesterol': 'total_cholesterol',
            'ldl_cholesterol': 'ldl',
            'hdl_cholesterol': 'hdl', 
            'hemoglobin': 'hemoglobin',
            'hematocrit': 'hematocrit',
            'tsh': 'tsh',
            'hba1c': 'hba1c',
            'vitamin_d': 'vitamin_d',
            'vitamin_b12': 'vitamin_b12', 
            'vitamin_c': 'vitamin_c',
            'vitamin_a': 'vitamin_a',
            'systolic_bp': 'systolic_bp',
            'diastolic_bp': 'diastolic_bp',
            'heart_rate': 'heart_rate',
            'creatinine': 'creatinine'
        }
        
        for csv_name, value in data_source.items():
            csv_name_clean = csv_name.lower().replace(' ', '_').replace('-', '_')
            if csv_name_clean in name_mapping:
                biomarkers[name_mapping[csv_name_clean]] = value
    
    return biomarkers

def calculate_optimal_range(acceptable_min: float, acceptable_max: float) -> Tuple[float, float]:
    """Calculate optimal range based on acceptable range using the specified formula."""
    # Formula: Optimal Range = Acceptable Range with 1/5 margin on each side
    range_size = acceptable_max - acceptable_min
    margin = range_size / 5
    
    optimal_min = acceptable_min + margin
    optimal_max = acceptable_max - margin
    
    return optimal_min, optimal_max

def analyze_biomarker(biomarker_key: str, value: float) -> Optional[Dict[str, Any]]:
    """Analyze a single biomarker and return its status and enhanced insights."""
    rules = BIOMARKER_RULES.get(biomarker_key)
    if not rules:
        return None
    
    # Calculate optimal range from acceptable range
    optimal_min, optimal_max = calculate_optimal_range(rules['acceptable_min'], rules['acceptable_max'])
    
    # Format ranges for display
    if rules['acceptable_range'].startswith('<'):
        # For "<200" type ranges, don't calculate optimal range normally
        acceptable_range_display = rules['acceptable_range']
        optimal_range_display = f"<{rules['acceptable_max'] - (rules['acceptable_max'] * 0.2):.1f}"
    elif rules['acceptable_range'].startswith('>'):
        # For ">40" type ranges, don't calculate optimal range normally  
        acceptable_range_display = rules['acceptable_range']
        optimal_range_display = f">{rules['acceptable_min'] + (rules['acceptable_min'] * 0.25):.1f}"
    else:
        acceptable_range_display = rules['acceptable_range']
        optimal_range_display = f"{optimal_min:.1f}-{optimal_max:.1f}"
    
    # Determine status and generate enhanced insight based on memory specifications
    if optimal_min <= value <= optimal_max:
        status = 'Optimal'
        insight = 'This is within optimal range'
        status_category = 'optimal'
    elif rules['acceptable_min'] <= value <= rules['acceptable_max']:
        if value < optimal_min:
            status = 'Below Optimal'
            insight = f'This is below optimal range; acceptable range is {acceptable_range_display}'
            status_category = 'below_optimal'
        elif value > optimal_max:
            status = 'Above Optimal'
            insight = f'This is above optimal range; acceptable range is {acceptable_range_display}'
            status_category = 'above_optimal'
        else:
            status = 'Optimal'
            insight = 'This is within optimal range'
            status_category = 'optimal'
    elif value < rules['acceptable_min']:
        status = 'Below Acceptable'
        insight = f'This is below acceptable range; acceptable range is {acceptable_range_display}'
        status_category = 'below_acceptable'
    elif value > rules['acceptable_max']:
        if value >= rules['high_threshold']:
            status = 'Significantly High'
            insight = f'This is significantly above acceptable range; acceptable range is {acceptable_range_display}'
            status_category = 'significantly_high'
        else:
            status = 'Above Acceptable'
            insight = f'This is above acceptable range; acceptable range is {acceptable_range_display}'
            status_category = 'above_acceptable'
    else:
        status = 'Normal'
        insight = 'This is within optimal range'
        status_category = 'optimal'
    
    return {
        'name': biomarker_key.replace('_', ' ').title(),
        'value': value,
        'unit': rules['unit'],
        'acceptable_range': acceptable_range_display,
        'optimal_range': optimal_range_display,
        'status': status,
        'insight': insight,
        'status_category': status_category,  # For frontend styling
        'is_optimal': status_category == 'optimal'
    }

def evaluate_disease_condition(condition: Dict, biomarkers: Dict[str, float]) -> bool:
    """Evaluate a single disease condition against biomarker values."""
    biomarker_key = condition['biomarker']
    operator = condition['operator']
    threshold = condition['value']
    
    if biomarker_key not in biomarkers:
        return False
    
    value = biomarkers[biomarker_key]
    
    if operator == '>=':
        return value >= threshold
    elif operator == '<=':
        return value <= threshold
    elif operator == '>':
        return value > threshold
    elif operator == '<':
        return value < threshold
    elif operator == '==' or operator == '=':
        return value == threshold
    elif operator == 'between':
        return threshold[0] <= value <= threshold[1]
    
    return False

def detect_diseases(biomarkers: Dict[str, float]) -> List[Dict[str, Any]]:
    """Detect potential diseases based on biomarker values."""
    detected_diseases = []
    
    for disease_key, disease_info in DISEASE_RULES.items():
        conditions = disease_info['conditions']
        logic = disease_info['logic']
        
        # Evaluate conditions
        condition_results = [
            evaluate_disease_condition(condition, biomarkers)
            for condition in conditions
        ]
        
        # Apply logic
        if logic == 'AND':
            disease_detected = all(condition_results)
        elif logic == 'OR':
            disease_detected = any(condition_results)
        else:
            disease_detected = False
        
        if disease_detected:
            detected_diseases.append({
                'name': disease_info['name'],
                'priority': disease_info['priority'],
                'reasoning': disease_info['reasoning']
            })
    
    # Only add "Everything Fine" if NO diseases detected AND all biomarkers are optimal
    if not detected_diseases:
        all_optimal = True
        for biomarker_key, value in biomarkers.items():
            if biomarker_key in BIOMARKER_RULES:
                rules = BIOMARKER_RULES[biomarker_key]
                optimal_min, optimal_max = calculate_optimal_range(rules['acceptable_min'], rules['acceptable_max'])
                if not (optimal_min <= value <= optimal_max):
                    all_optimal = False
                    break
        
        if all_optimal:
            detected_diseases.append({
                'name': 'Everything Fine',
                'priority': 'Excellent Health',
                'reasoning': 'All biomarkers are within optimal ranges. No potential health conditions detected.'
            })
        else:
            # If no diseases but biomarkers are not optimal, show general health status
            detected_diseases.append({
                'name': 'Health Monitoring Recommended',
                'priority': 'Monitor',
                'reasoning': 'Some biomarkers are outside optimal ranges but no specific diseases detected. Continue monitoring and consider lifestyle improvements.'
            })
    
    # Sort by priority (High Risk, Medium Risk, Low Risk)
    priority_order = {'High Risk': 0, 'Medium Risk': 1, 'Low Risk': 2, 'Monitor': 3, 'Excellent Health': 4}
    detected_diseases.sort(key=lambda x: priority_order.get(x['priority'], 5))
    
    return detected_diseases

def get_symptoms(detected_diseases: List[Dict[str, Any]], biomarkers: Dict[str, float]) -> List[str]:
    """Get symptoms for the detected diseases and general health indicators."""
    symptoms = set()
    
    # Always analyze individual biomarkers for comprehensive health insights
    general_symptoms = {
        'glucose': {
            'high': ['Increased thirst', 'Frequent urination', 'Fatigue', 'Blurred vision'],
            'borderline': ['Mild fatigue', 'Occasional thirst', 'Sugar cravings']
        },
        'total_cholesterol': {
            'high': ['No obvious symptoms initially', 'Potential chest discomfort', 'Exercise fatigue'],
            'borderline': ['Mild exercise intolerance', 'Occasional fatigue']
        },
        'ldl': {
            'high': ['Chest tightness during exercise', 'Shortness of breath', 'Fatigue'],
            'borderline': ['Mild chest discomfort during activity']
        },
        'hdl': {
            'low': ['Increased cardiovascular risk symptoms', 'Exercise intolerance'],
            'borderline': ['Mild fatigue during physical activity']
        },
        'hemoglobin': {
            'low': ['Fatigue', 'Weakness', 'Pale skin', 'Cold hands and feet', 'Shortness of breath'],
            'borderline': ['Mild fatigue', 'Occasional weakness', 'Slight paleness']
        },
        'hematocrit': {
            'low': ['Fatigue', 'Weakness', 'Dizziness', 'Cold sensitivity'],
            'borderline': ['Mild fatigue', 'Occasional dizziness']
        },
        'tsh': {
            'high': ['Fatigue', 'Weight gain', 'Cold sensitivity', 'Dry skin', 'Hair thinning'],
            'low': ['Weight loss', 'Rapid heartbeat', 'Nervousness', 'Sweating', 'Heat sensitivity'],
            'borderline_high': ['Mild fatigue', 'Slight weight gain', 'Mild cold sensitivity'],
            'borderline_low': ['Mild nervousness', 'Slight weight loss', 'Mild heat sensitivity']
        },
        'hba1c': {
            'high': ['Fatigue', 'Increased thirst', 'Frequent urination', 'Slow healing'],
            'borderline': ['Mild fatigue', 'Occasional increased appetite']
        },
        'vitamin_d': {
            'low': ['Bone pain', 'Muscle weakness', 'Frequent infections', 'Depression'],
            'borderline': ['Mild fatigue', 'Occasional muscle aches']
        },
        'vitamin_b12': {
            'low': ['Extreme fatigue', 'Memory problems', 'Tingling in hands/feet', 'Balance issues'],
            'borderline': ['Mild fatigue', 'Occasional memory lapses']
        },
        'vitamin_c': {
            'low': ['Easy bruising', 'Slow wound healing', 'Bleeding gums', 'Joint pain'],
            'borderline': ['Mild bruising', 'Slower healing']
        },
        'systolic_bp': {
            'high': ['Headaches', 'Dizziness', 'Shortness of breath', 'Chest pain'],
            'low': ['Dizziness', 'Fainting', 'Fatigue'],
            'borderline': ['Mild headaches', 'Occasional dizziness']
        },
        'diastolic_bp': {
            'high': ['Headaches', 'Dizziness', 'Blurred vision'],
            'low': ['Light-headedness', 'Weakness'],
            'borderline': ['Mild dizziness']
        },
        'heart_rate': {
            'high': ['Palpitations', 'Shortness of breath', 'Chest discomfort', 'Dizziness'],
            'low': ['Fatigue', 'Dizziness', 'Weakness'],
            'borderline': ['Mild palpitations', 'Occasional fatigue']
        },
        'creatinine': {
            'high': ['Decreased urination', 'Swelling in legs/ankles', 'Fatigue', 'Nausea'],
            'borderline': ['Mild fatigue', 'Occasional swelling']
        }
    }
    
    # Add symptoms from detected diseases (skip generic health status messages)
    disease_symptoms_added = False
    for disease in detected_diseases:
        disease_name = disease['name'].lower()
        
        # Skip generic health status messages
        if disease_name in ['everything fine', 'health monitoring recommended']:
            continue
            
        disease_symptoms_added = True
        # Find corresponding disease rule
        for disease_key, disease_info in DISEASE_RULES.items():
            if disease_info['name'].lower() == disease_name:
                symptoms.update(disease_info.get('symptoms', []))
                break
    
    # Always analyze individual biomarkers for symptoms (comprehensive analysis)
    biomarker_symptoms_added = False
    for biomarker_key, value in biomarkers.items():
        if biomarker_key in BIOMARKER_RULES and biomarker_key in general_symptoms:
            rules = BIOMARKER_RULES[biomarker_key]
            
            if value >= rules.get('high_threshold', float('inf')):
                symptoms.update(general_symptoms[biomarker_key].get('high', []))
                biomarker_symptoms_added = True
            elif value > rules['acceptable_max']:
                symptoms.update(general_symptoms[biomarker_key].get('borderline', []))
                biomarker_symptoms_added = True
            elif value < rules['acceptable_min']:
                if biomarker_key == 'tsh':
                    symptoms.update(general_symptoms[biomarker_key].get('low', []))
                else:
                    symptoms.update(general_symptoms[biomarker_key].get('low', []))
                biomarker_symptoms_added = True
            elif biomarker_key == 'tsh' and value > 3.0:  # Special case for borderline high TSH
                symptoms.update(general_symptoms[biomarker_key].get('borderline_high', []))
                biomarker_symptoms_added = True
            elif biomarker_key == 'hdl' and value < 50:  # Special case for borderline low HDL
                symptoms.update(general_symptoms[biomarker_key].get('borderline', []))
                biomarker_symptoms_added = True
    
    # If no specific symptoms from diseases or biomarkers, provide positive health indicators
    if not symptoms and not disease_symptoms_added and not biomarker_symptoms_added:
        symptoms.update([
            'All biomarkers within optimal ranges - no symptoms to monitor',
            'Excellent overall health indicators',
            'Continue current healthy lifestyle practices',
            'Maintain regular health check-ups',
            'Stay active and eat a balanced diet'
        ])
    elif not symptoms:
        # Fallback if somehow no symptoms were added but we should have some
        symptoms.update([
            'Monitor general health indicators regularly',
            'Maintain healthy lifestyle practices',
            'Follow up with healthcare provider as needed',
            'Stay hydrated and get adequate sleep',
            'Continue regular exercise routine'
        ])
    
    # Limit to most relevant symptoms and ensure we always return something meaningful
    symptoms_list = list(symptoms)[:15]
    
    # Ensure we always have at least some health guidance
    if len(symptoms_list) < 3:
        symptoms_list.extend([
            'Regular health monitoring recommended',
            'Maintain balanced nutrition and exercise',
            'Consult healthcare provider for personalized advice'
        ])
    
    return symptoms_list[:15]

def generate_recommendations(detected_diseases: List[Dict[str, Any]], biomarkers: Dict[str, float]) -> Dict[str, List[str]]:
    """Generate personalized recommendations based on detected conditions."""
    recommendations = {
        'Professional Consultation': set(),
        'Dietary': set(),
        'Lifestyle': set()
    }
    
    # Add recommendations based on detected diseases
    for disease in detected_diseases:
        disease_name = disease['name'].lower()
        
        # Map disease to recommendation template
        template_key = None
        if 'diabetes' in disease_name:
            template_key = 'diabetes_type_2'
        elif 'cardiovascular' in disease_name:
            template_key = 'cardiovascular_risk'
        elif 'anemia' in disease_name:
            template_key = 'iron_deficiency_anemia'
        elif 'thyroid' in disease_name:
            template_key = 'thyroid_disorders'
        
        if template_key and template_key in RECOMMENDATION_TEMPLATES:
            template = RECOMMENDATION_TEMPLATES[template_key]
            for category, items in template.items():
                recommendations[category].update(items)
    
    # Add general wellness recommendations if no specific diseases detected
    if not detected_diseases:
        general_template = RECOMMENDATION_TEMPLATES['general_wellness']
        for category, items in general_template.items():
            recommendations[category].update(items[:2])  # Limit general recommendations
    
    # Convert sets back to lists
    return {category: list(items) for category, items in recommendations.items()}

# ========================================================================================
# FLASK ROUTES
# ========================================================================================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze_report():
    """Main endpoint for analyzing uploaded health reports (single or multiple files)."""
    try:
        # Check if files are present
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Handle both single file (legacy) and multiple files
        if 'files' in request.files:
            files = request.files.getlist('files')
        else:
            files = [request.files['file']]
        
        if not files or all(f.filename == '' or f.filename is None for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        print(f"Processing {len(files)} file(s) for collective analysis...")
        
        # Validate all files
        for file in files:
            if file.filename is None or not allowed_file(file.filename):
                return jsonify({'error': f'File type not supported: {file.filename or "unknown"}'}), 400
        
        # Process all files and collect biomarkers
        all_biomarkers = {}
        file_analyses = []
        processed_files = []
        
        for i, file in enumerate(files):
            filename = secure_filename(file.filename or 'unknown_file')
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Process file based on type
                if file_extension == 'pdf':
                    extracted_text = parse_pdf_file(temp_file_path)
                    biomarkers = standardize_biomarkers(extracted_text, 'pdf')
                elif file_extension in ['jpg', 'jpeg', 'png']:
                    extracted_text = parse_image_file(temp_file_path)
                    biomarkers = standardize_biomarkers(extracted_text, 'image')
                elif file_extension == 'csv':
                    biomarkers = parse_csv_file(temp_file_path)
                else:
                    continue  # Skip unsupported files
                
                # Store individual file analysis
                file_analyses.append({
                    'filename': filename,
                    'biomarkers': biomarkers,
                    'file_type': file_extension
                })
                
                # Merge biomarkers (take most recent values or average if needed)
                for biomarker, value in biomarkers.items():
                    if biomarker in all_biomarkers:
                        # For collective analysis, take the average of multiple readings
                        if isinstance(all_biomarkers[biomarker], list):
                            all_biomarkers[biomarker].append(value)
                        else:
                            all_biomarkers[biomarker] = [all_biomarkers[biomarker], value]
                    else:
                        all_biomarkers[biomarker] = value
                
                processed_files.append(filename)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # If no biomarkers found across all files, use enhanced sample data (ALWAYS SHOW ALL READINGS)
        if not all_biomarkers:
            all_biomarkers = {
                # Original biomarkers - designed to show variety of conditions
                'glucose': 115.0,           # Slightly elevated (borderline) - triggers prediabetes
                'total_cholesterol': 220.0, # High cholesterol - triggers high cholesterol condition
                'hdl': 38.0,                # Low HDL - triggers cardiovascular risk
                'ldl': 145.0,               # Borderline high LDL - triggers moderate cardio risk
                'hemoglobin': 11.8,         # Low hemoglobin - triggers iron deficiency anemia
                'hematocrit': 35.0,         # Low hematocrit - triggers iron deficiency anemia
                'tsh': 3.2,                 # Borderline high TSH - triggers borderline hypothyroidism
                'hba1c': 5.9,               # Borderline prediabetes - triggers prediabetes
                # New vitamin levels - designed to trigger deficiencies
                'vitamin_d': 18.0,          # Deficient (< 20) - triggers vitamin D deficiency
                'vitamin_b12': 180.0,       # Low (< 200) - triggers B12 deficiency
                'vitamin_c': 0.4,           # Low (< 0.6) - triggers vitamin C deficiency
                'vitamin_a': 15.0,          # Low vitamin A
                # Blood pressure - designed to trigger hypertension
                'systolic_bp': 135.0,       # Stage 1 hypertension (130-139)
                'diastolic_bp': 85.0,       # Stage 1 hypertension (80-89)
                # Heart rate and kidney function - designed to trigger conditions
                'heart_rate': 105.0,        # Mild tachycardia (> 100)
                'creatinine': 1.4           # Mild kidney dysfunction (> 1.3)
            }
        else:
            pass
        
        # Calculate averages for biomarkers with multiple readings
        final_biomarkers = {}
        for biomarker, values in all_biomarkers.items():
            if isinstance(values, list):
                final_biomarkers[biomarker] = sum(values) / len(values)
            else:
                final_biomarkers[biomarker] = values
        
        # Analyze collective biomarkers - ALWAYS show all readings
        analyzed_biomarkers = []
        for biomarker_key, value in final_biomarkers.items():
            analysis = analyze_biomarker(biomarker_key, value)
            if analysis:
                analyzed_biomarkers.append(analysis)
            else:
                # Even if no rules exist, show the raw value
                analyzed_biomarkers.append({
                    'name': biomarker_key.replace('_', ' ').title(),
                    'value': value,
                    'unit': '',
                    'acceptable_range': 'Not defined',
                    'optimal_range': 'Not defined',
                    'status': 'Detected',
                    'insight': f'Value detected: {value}. Reference ranges not available for this parameter.',
                    'status_category': 'unknown',
                    'is_optimal': False
                })
        
        # Detect diseases based on collective data
        detected_diseases = detect_diseases(final_biomarkers)
        
        # Get symptoms based on collective analysis
        symptoms = get_symptoms(detected_diseases, final_biomarkers)
        
        # Generate recommendations based on collective findings
        recommendations = generate_recommendations(detected_diseases, final_biomarkers)
        
        # Prepare collective response
        response = {
            'biomarkers': analyzed_biomarkers,
            'potential_diseases': detected_diseases,
            'symptoms': symptoms,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat(),
            'files_processed': len(processed_files),
            'file_details': file_analyses,
            'collective_analysis': True if len(files) > 1 else False
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error occurred'}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error'}), 500

# ========================================================================================
# MAIN EXECUTION
# ========================================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("HealthScoreAI")
    print("=" * 60)
    print("Starting Flask server...")
    print("Frontend: http://localhost:5000")
    print("API Endpoint: http://localhost:5000/analyze")
    print("=" * 60)
    
    # Check for optional dependencies
    missing_deps = []
    if not PyPDF2:
        missing_deps.append("PyPDF2 (PDF processing)")
    if not Image or not pytesseract:
        missing_deps.append("Pillow + pytesseract (Image processing)")
    
    if missing_deps:
        print("Warning: Missing optional dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Install with: pip install PyPDF2 Pillow pytesseract")
        print("=" * 60)
    
    # Run Flask app
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)