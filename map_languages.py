import pandas as pd

df = pd.read_csv("data/all_reviews.csv")

lang = {0: 'DA', 1: 'EN', 2: 'RU', 3: 'IT', 4: 'PT', 6: 'EL', 7: 'FR', 8: 'JA', 9: 'NL', 10: 'TR', 11: 'ZH', 12: 'ES',
        13: 'DE', 14: 'RO', 16: 'AR', 18: 'BG', 19: 'KO', 21: 'LT', 22: 'CA', 23: 'LT', 24: 'CE', 26: 'DA', 28: 'DA',
        29: 'PL', 30: 'NO', 31: 'FA', 34: 'SV',32: 'SK', 33: 'FI', 35: 'SL', 36: 'SV', 37: 'ES', 41: 'TH', 42: 'HR',
        43: 'FIL', 44: 'HU', 45: 'ID', 46: 'UK',47: 'VI', 48: 'HE', 49: 'SQ', 50: 'KA', 51: 'DA', 52: 'IS', 53: 'GA',
        55: 'DA'}

df['lang_code'] = df['lang']
df = df.replace({'lang_code': lang})

df.to_csv("data/all_reviews.csv")
