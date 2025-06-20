import multiprocessing
import pandas as pd
import sys
from copy import deepcopy
from datetime import datetime
import numpy as np
from dtw import dtw
import subprocess
import argparse 
from geotagre import match_timestamps_idx, insert_new_match, conduct_dtw, run_command

parser = argparse.ArgumentParser(description="Match datetime with GPS")
parser.add_argument("-gps", "--gps_csv", help="Path to gps csv file")
parser.add_argument("-exif", "--img_exif", help="Path to image exif csv")
parser.add_argument("-n", "--num_cpu", help="Number of cpu for processing")
parser.add_argument("-o", "--output_csv", help="output csv name", default = "OUTPUT.csv" )
args = parser.parse_args()

try:
    gps_data_path = args.gps_csv
    print(f"path to gps data:{gps_data_path}")
    gps_df = pd.read_csv(gps_data_path)
    camera_path = args.img_exif
    print(f"path to camera data: {camera_path}")
    camera_df = pd.read_csv(camera_path)
    num_cpu = int(args.num_cpu)
    outfile_name = args.output_csv

except Exception as e:
    print(f"Error {e}")
    sys.exit(1)


matching_idx = list() 
ls_result_df = list() 
ls_avg_time_diff = list()
ls_ascending = list()
print("Direct matching in ascending order of camera date time...")
TF_=True
ls_matching_ = match_timestamps_idx(gps_df, camera_df, ASCENDING_TF=TF_, 
                                    colname_camera = "updated_datetime"
                                   )#"DateTimeOriginal")
df_out, avg_time_diff = insert_new_match(gps_df, camera_df,  ls_matching_, ASCENDING_TF = TF_, 
                                         camera_dt_col = "updated_datetime",#DateTimeOriginal",
                                        file_path_col = 'SourceFile'
                                        )
ls_result_df += [df_out]
matching_idx += [ls_matching_]
ls_avg_time_diff += [avg_time_diff]
ls_ascending += [TF_]
print("Direct matching in descending order of camera date time...")
TF_=False    
ls_matching_ = match_timestamps_idx(gps_df, camera_df, ASCENDING_TF=TF_, 
                                    colname_camera = "updated_datetime"
                                   )#"DateTimeOriginal")
df_out, avg_time_diff = insert_new_match(gps_df, camera_df,  ls_matching_, ASCENDING_TF = TF_, 
                                         camera_dt_col = "updated_datetime", #"DateTimeOriginal",
                                        file_path_col = 'SourceFile'
                                        )
IS_DF_SAME = ls_result_df[0].equals(df_out)

if not IS_DF_SAME:
    print("Different matching is obtained by sorting order (ascending vs descending). Adding both indices...")
    matching_idx += [ls_matching_]
    ls_avg_time_diff += [avg_time_diff]
    ls_result_df += [df_out]
    ls_ascending += [TF_]

try:
    print("Attempting Dynamic Time Wrapping...")
    dtw_idx = conduct_dtw(
        gps_df,
        camera_df,
        camera_dt_col = 'updated_datetime',
        ASCENDING_TF = True
    )
    result_df_dtw, _ = insert_new_match(gps_df, camera_df, dtw_idx, ASCENDING_TF = True, 
                                        camera_dt_col = "updated_datetime", #"DateTimeOriginal",
                                       file_path_col = 'SourceFile')
    
    for df_cand_ in ls_result_df:
        IS_DF_SAME = result_df_dtw.equals(df_cand_)
        if IS_DF_SAME:
            DONT_ADD_DTW = True
        else:
            DONT_ADD_DTW = False
    
    if not DONT_ADD_DTW:
        print("Different matching order is obtained by Dynamic Time Wrapping. Adding...")
        ls_result_df += [result_df_dtw]
        matching_idx += [dtw_idx]
        ls_avg_time_diff += [avg_time_diff]
        ls_ascending += [True]
    else:
        print("Dynamic time wrapping yields the same matching as the above. Skipping...")

except Exception as e:
    print(f"Error: {e} Dynamic Time Wrapping Failed.")
min_avg_time_diff = np.min(ls_avg_time_diff)
print(f"Min Avg Time Difference: {min_avg_time_diff:.3f} seconds. Outputing Data Frame...")
win_idx = np.where(ls_avg_time_diff==min_avg_time_diff)[0][0]

fin_result = ls_result_df[win_idx]
fin_idx = matching_idx[win_idx]
fin_order = ls_ascending[win_idx]
fin_timediff = ls_avg_time_diff[win_idx]

print('Done matching camera datetime with GPS.')
# print(fin_result, fin_idx, fin_order) 

fin_result.to_csv(outfile_name)
print(f"Outputed data Frame to: {outfile_name}.")

gps_lat_col = 'latitude'
gps_long_col = 'longitude'
gps_alti_col = 'altitude'
gps_az_col = 'az'
camera_dt_col = 'adjusted_camera_datetime'
file_path_col = 'SourceFile'

exif_mapping = dict()
exif_mapping[gps_lat_col] = 'GPSLatitude'
exif_mapping[gps_long_col] = 'GPSLongitude'
exif_mapping[gps_alti_col] = 'GPSAltitude'
exif_mapping[gps_az_col] = 'GPSImgDirection'
exif_mapping[camera_dt_col] = 'DateTimeOriginal'
exif_mapping[file_path_col] = 'SourceFile'

fin_trim = fin_result[list(exif_mapping.keys())].rename(columns=exif_mapping)

fin_trim = fin_trim.dropna( subset = [file_path_col])


print(
    fin_trim
)

print('Geotagging files...')

ls_cli_commands = list()

for index, row in fin_trim.iterrows():
    cli_command = ["exiftool"]
    for field_ in list(exif_mapping.values()):
        if field_=='SourceFile':
            pass 
        elif field_=='DateTimeOriginal':
            cli_command += [f"-{field_}={row[field_]}"]
        elif field_=='GPSImgDirection':
            cli_command += [f"-{field_}={row[field_]}", f"-{field_}Ref=T"]
        else:
            cli_command += [f"-{field_}={row[field_]}", f"-{field_}Ref={row[field_]}"]        
    cli_command += [f"{row['SourceFile']}"]
    
    ls_cli_commands += [cli_command]

with multiprocessing.Pool(processes = num_cpu) as pool:
    results = pool.map(run_command, ls_cli_commands)
