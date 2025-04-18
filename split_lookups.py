import os
import pandas as pd
from utils import split_csv

script_dir = os.path.dirname(os.path.abspath(__file__))
split_lookups = os.path.join(script_dir, 'Split_Lookup_Lists')
#parameterize the split_lookup file name?

input_file = os.path.join(script_dir,'download_variables.csv')

split_csv(input_file, split_lookups)