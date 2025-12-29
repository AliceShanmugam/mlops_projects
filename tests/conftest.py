# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:26:16 2025

@author: coach
"""

import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
