# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 17:25:13 2025

@author: coach
"""

import pandas as pd

def test_can_read_raw_data():
    X = pd.read_csv("data/raw/X_train_update.csv")
    y = pd.read_csv("data/raw/Y_train_CVw08PX.csv")
    assert len(X) > 0
    assert len(y) > 0
