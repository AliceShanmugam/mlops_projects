## Raw data quality report

    RangeIndex: 84916 entries, 0 to 84915
    Data columns (total 5 columns):
    #   Column       Non-Null Count  Dtype 
    ---  ------       --------------  ----- 
    0   designation  84916 non-null  object
    1   description  55116 non-null  object
    2   productid    84916 non-null  int64 
    3   imageid      84916 non-null  int64 
    4   prdtypecode  84916 non-null  int64 
    dtypes: int64(3), object(2)
    memory usage: 3.2+ MB


    prdtypecode
    2583    10209
    1560     5073
    1300     5045
    2060     4993
    2522     4989
    1280     4870
    2403     4774
    2280     4760
    1920     4303
    1160     3953
    1320     3241
    10       3116
    2705     2761
    1140     2671
    2582     2589
    40       2508
    2585     2496
    1302     2491
    1281     2070
    50       1681
    2462     1421
    2905      872
    60        832
    2220      824
    1301      807
    1940      803
    1180      764

## (A continuer pour la data nettoyé)

### Source des données
- Origine : ...
- Date d’extraction : ...
- Nombre de lignes : 120 000

### Qualité
| Check | Résultat |
|----|----|
| Valeurs manquantes | 2.3% |
| Duplicats | 1.1% |
| Outliers | Traitement IQR |

### Actions
- Suppression des doublons
- Imputation médiane
- Encodage One-Hot