def test_prediction_range(preds):
    assert preds.min() >= 0
    assert preds.max() <= 1