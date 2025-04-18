import pandas as pd
import numpy as np
from arcgis.features import FeatureLayer
import os
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import arcpy



# Gets data with query from the TRPA server
def get_fs_data_query(service_url, query_params):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query(query_params)
    # Convert the query result to a list of dictionaries
    feature_list = query_result.features
    # Create a pandas DataFrame from the list of dictionaries
    all_data = pd.DataFrame([feature.attributes for feature in feature_list])
    # return data frame
    return all_data


# Gets data from the TRPA server
def get_fs_data(service_url):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query()
    # Convert the query result to a list of dictionaries
    feature_list = query_result.features
    # Create a pandas DataFrame from the list of dictionaries
    all_data = pd.DataFrame([feature.attributes for feature in feature_list])
    # return data frame
    return all_data


# Gets spatially enabled dataframe from TRPA server
def get_fs_data_spatial(service_url):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query().sdf
    return query_result


# Gets spatially enabled dataframe with query
def get_fs_data_spatial_query(service_url, query_params):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query(query_params).sdf
    return query_result
def spatial_join_map(target, source, join_field,  map_field, target_field):
    # spatial join
    arcpy.SpatialJoin_analysis(target, source, 'memory\\temp', 
                               'JOIN_ONE_TO_ONE', 'KEEP_ALL','HAVE_THEIR_CENTER_IN')
    # get result as a spatial dataframe
    join = pd.DataFrame.spatial.from_featureclass('memory\\temp')
    join.info()
    # map values
    target[target_field] = target[join_field].map(dict(zip(join[join_field], join[map_field])))
    return target

def split_csv(file_path, output_folder):
    # Read the full CSV into a DataFrame
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    
    # Get the base file name without extension
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Define the number of rows per split file (not counting the header)
    rows_per_file = 2
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Loop to create each smaller CSV
    for i in range(0, len(df), rows_per_file):
        # Select the current chunk of rows
        df_chunk = df.iloc[i:i + rows_per_file]
        
        # Create the output file path with the base name and part number
        output_file = os.path.join(output_folder, f"{base_name}_part_{i // rows_per_file + 1}.csv")
        
        # Write the chunk to a new CSV, including the header
        df_chunk.to_csv(output_file, index=False)
        print(f"Created {output_file}")

