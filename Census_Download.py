import pandas as pd
import numpy as np
import requests
import pyodbc
import arcpy
import os
from arcgis.features import FeatureLayer
import glob
import gc
import shutil
from utils import *
# This is using Andy's Census API KEy
census_api_key = '9a73d08c296b844e58f1c70bd19c831826da5cbf'


# Need to define datatypes so that FIPS code doesn't get cast as int and drop leading 0s
dtypes = {
    'YEAR' : str,
    'STATE': str,
    'GEOGRAPHY': str,
    'GEOID': str,
    'TRPAID':str,
    'NEIGHBORHOOD': str
}

#Manually defined list of census tracts that are within the basin
 
service_url = 'https://maps.trpa.org/server/rest/services/Demographics/MapServer/27'

feature_layer = FeatureLayer(service_url)
tahoe_geometry_fields = ['YEAR', 'STATE', 'GEOGRAPHY', 'GEOID', 'TRPAID', 'NEIGHBORHOOD']
query_result = feature_layer.query(out_fields=",".join(tahoe_geometry_fields))
# Convert the query result to a list of dictionaries
feature_list = query_result.features

# Create a pandas DataFrame from the list of dictionaries
tahoe_geometry = pd.DataFrame([feature.attributes for feature in feature_list])

#Helper function that is used to concatenate census data return
def create_or_append_df(df, summary_df):
    if df.empty:
        df = summary_df.copy()
    else:
        df = pd.concat([df, summary_df], ignore_index=True)
    return df

#This gets the result of the get request and does some data wrangling to make it fit our structure
def get_request_census(request_url, sample_level, geo_name):
    response = requests.get(request_url)
    #print(response.status_code)
    df = pd.DataFrame(response.json())
    #The json returns column names in the first row
    df.columns = df.iloc[0]
    df = df[1:]
    df['sample_level']=sample_level
    df['Geo_Name']=geo_name
    #Might as well add counties and states at this stage
    return df

def get_variable_data(year, dataset, geometry_return, variable, variablename, census_api_key, census_geom_year, tahoe_geometry, variable_category):
    #Returns all data for a given dataset for Washoe, El Dorado, Carson City, Douglas, Placer Counties
    #Need to make five seperate api calls because of the geometry structure
    county_states ={
        '06': ['017','061'],
        '32': ['005', '031']

    }
    base_url = 'https://api.census.gov/data'
    df_total=pd.DataFrame()
    #Formatting to match html get request
    geometry_return=geometry_return.replace(" ", "%20")
    #This adds tract level to make block groups or blocks get request valid
    if geometry_return == 'tract':
        geometry_level = ''
    else:
        geometry_level='%20tract:*'
    if 'acs/acs5' in dataset:
        variable= variable +'E,'+variable + 'M'

    
    for state in county_states:
        for county in county_states[state]:
            print(f'{base_url}/{year}/{dataset}?get=GEO_ID,{variable}&for={geometry_return}:*&in=state:{state}%20county:{county}{geometry_level}&key={census_api_key}')
            request_url = f"{base_url}/{year}/{dataset}?get=GEO_ID,{variable}&for={geometry_return}:*&in=state:{state}%20county:{county}{geometry_level}&key={census_api_key}"
            response = requests.get(request_url)
            
            df = pd.DataFrame(response.json())
            #The json returns column names in the first row
            df.columns = df.iloc[0]
            df = df[1:]
            #Might as well add counties and states at this stage
            if df_total.empty:
                df_total=df
            else:
                df_total=pd.concat([df_total, df])
    #Figure out exactly what variable we want here
    #Add something here to handle margin of error
    df_total['variable_code']=variable
    df_total['variable_name']=variablename
    df_total['variable_category']= variable_category
    df_total['year_sample']=year
    df_total['sample_level']=geometry_return.replace("%20", " ")
    df_total['dataset']= dataset
    df_total['census_geom_year'] = census_geom_year
    df_total['GEO_ID'] = df_total['GEO_ID'].str.split('US').str[1]
    df_total['TRPAID'] = df_total['GEO_ID']+df_total['census_geom_year'].astype(str)
    df_total.columns.values[1] = 'value'
    df_total['value'] = df_total['value'].astype(float)
    if 'acs/acs5' in dataset:
        df_total.columns.values[2]='MarginOfError'
        df_total['variable_code'] = df_total['variable_code'].str.split(',').str[0]
    else:
        df_total.insert(2, 'MarginOfError', np.NaN)
    if geometry_return == 'tract':
        tract_col_loc = df_total.columns.get_loc('tract')
        df_total.insert(tract_col_loc, 'block group', np.NaN)

    #filter to just the tahoe parcels
    df_total = df_total[df_total['TRPAID'].isin(tahoe_geometry['TRPAID'])]
    df_total =  pd.merge(df_total, tahoe_geometry[['TRPAID', 'NEIGHBORHOOD']], on='TRPAID', how= 'left')
    
    return df_total

def census_download_wrapper (variable_file):
    dtypes = {
    'Variable' : str,
    'Code': str,
    'Category': str,
    'Datasource': str,
    'CodeNumber':str,
    'Year':str,
    'census_geom_year':str,
    'GeometryLevel':str
    }


    variables = pd.read_csv(variable_file,dtype=dtypes)

    #Loop through this?
    df_values=pd.DataFrame()
    for index, row in variables.iterrows():
        #print(index)
        
        df = get_variable_data(row['Year'], row['Datasource Name'],row['GeometryLevel'],row['CodeNumber'],row['Variable'], census_api_key, row['census_geom_year'], tahoe_geometry, row['Category'])
        
        df_values = create_or_append_df(df_values, df)
    return df_values

#Import all csvs from a folder and merge them into a single dataframe
def import_csvs(folder_path):
    import os
    import glob
    os.chdir(folder_path)
    extension = 'csv'
    all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
    #combine all files in the list
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ])
    return combined_csv

script_dir = os.path.dirname(__file__)
split_lookups = os.path.join(script_dir, 'Split_Lookup_Lists')
download_folder = os.path.join(script_dir, 'Downloaded_Data')
processed_folder = os.path.join(script_dir, 'Completed_Lookup_Lists')



os.makedirs(download_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)

for file_path in glob.glob(os.path.join(split_lookups, '*.csv')):
        # Read the CSV into a DataFrame
        #df = pd.read_csv(file_path)
        
        # Process the DataFrame with the provided function
        df = census_download_wrapper(file_path)
                # Modify the output file name to include "_2" before the file extension
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        # Save the processed DataFrame to the output folder with the same file name
        output_file_path = os.path.join(download_folder, f"{base_name}_2{ext}")
        
        # Save the processed DataFrame to the output folder
        df.to_csv(output_file_path, index=False)
        print(f"Processed and saved: {output_file_path}")
        
        # Move the original file to the processed folder
        processed_file_path = os.path.join(processed_folder, os.path.basename(file_path))
        shutil.move(file_path, processed_file_path)
        del df
        gc.collect()
        #print(f"Moved original file to: {processed_file_path}")