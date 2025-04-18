import pandas as pd
import numpy as np
import arcpy
from arcgis.features import FeatureLayer
from utils import sum_multiple_variables
service_url = 'https://maps.trpa.org/server/rest/services/Demographics/MapServer/27'

feature_layer = FeatureLayer(service_url)
tahoe_geometry_fields = ['YEAR', 'STATE', 'GEOGRAPHY', 'GEOID', 'TRPAID', 'NEIGHBORHOOD']
query_result = feature_layer.query(out_fields=",".join(tahoe_geometry_fields))
# Convert the query result to a list of dictionaries
feature_list = query_result.features

# Create a pandas DataFrame from the list of dictionaries
tahoe_geometry = pd.DataFrame([feature.attributes for feature in feature_list])

county_lookup = {
    '005': 'Douglas County (Tahoe Basin)',
    '017': 'El Dorado County (Tahoe Basin)',
    '031': 'Washoe County (Tahoe Basin)',
    '061': 'Placer County (Tahoe Basin)'
}

state_lookup = {
    '32': 'Nevada',
    '06': 'California'
}

inflation_adjustment = {
    '2000': 1.57,
    '2010': 1.24
}

service_url = 'https://maps.trpa.org/server/rest/services/Demographics/MapServer/28'

feature_layer = FeatureLayer(service_url)
query_result = feature_layer.query()
# Convert the query result to a list of dictionaries
feature_list = query_result.features

# Create a pandas DataFrame from the list of dictionaries
all_data = pd.DataFrame([feature.attributes for feature in feature_list])

all_data_clean = all_data.loc[(all_data['county']!='510')&(all_data['value']>=0)]
all_data_clean.loc[all_data_clean['county'].isin(['005','017']),'north_south'] = 'South Lake'
all_data_clean.loc[all_data_clean['county'].isin(['031','061']),'north_south'] = 'North Lake'
all_data_clean['county_name'] = all_data_clean['county'].apply(lambda x: county_lookup.get(x, None))
all_data_clean['state_name'] = all_data_clean['state'].apply(lambda x: state_lookup.get(x, None))


all_data_clean = all_data_clean.dropna(subset='value')

summary_variable_list = pd.read_csv('summary_variable_list.csv')
filterd_data = all_data_clean[all_data_clean['variable'].isin(summary_variable_list['variable'])&(all_data_clean['year'].isin(summary_variable_list['year']))]

summed_data = sum_multiple_variables(filterd_data, 'variable', summary_variable_list)

summed_data.to_csv('summed_data.csv', index=False)
