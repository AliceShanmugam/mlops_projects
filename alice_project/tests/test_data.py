def test_no_missing_values(df):
    assert df.isnull().sum().sum() == 0