from datetime import date
from app.calendar import advance_month

def test_september_to_october():
    assert advance_month(date(1900,9,1)) == date(1900,10,1)

def test_december_to_january():
    assert advance_month(date(1900,12,1)) == date(1901,1,1)
