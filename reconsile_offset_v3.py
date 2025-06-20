# reconsile_offset_v3

import json
import sys
import argparse
import datetime
from copy import deepcopy
import glob
import tqdm
import os
import pandas as pd
from geotagre import *

parser = argparse.ArgumentParser(description="correct offsets and update datetime in exif")
parser.add_argument("-gps", "--gps_csv", help="Path to gps csv file")
parser.add_argument("-exif", "--img_exif", help="Path to image exif csv")
args = parser.parse_args()
#sys.argv
csv_path = args.img_exif
# json_path = args.img_exif

gps_dt_col_ = 'datetime'
camera_dt_col_ = 'DateTimeOriginal'
fn_col_ = 'SourceFile'
reg_dt_format = "%Y-%m-%d %H:%M:%S"
camera_dt_format = "%Y:%m:%d %H:%M:%S"
dt_format_ms = "%Y-%m-%d %H:%M:%S.%f"

# # open json file
# try:
#     with open(json_path, "r") as f:
#         json_dat = json.load(f)
# except Exception as e:
#     print(f"Error: {e}; supply correct path to json file.")
#     sys.exit(1)
# # open csv file
# try: 
#     df_exif_ = pd.read_csv(csv_path)
# except Exception as e:
#     print(f"Error: {e}; reading pandas caused errors.")
#     sys.exit(1)
try:
    print(f'Reading GPS log from "{args.gps_csv}"...')
    df_gps = pd.read_csv(args.gps_csv)
    print(f'Reading Image exif information from "{args.img_exif}"...')
    df_img_exif = pd.read_csv(args.img_exif)
except Exception as e:
    print(f"Error: {e}; reading csv files caused errors.")
    
json_dat = extract_datetime_to_dict(df_gps, 
                         df_img_exif,
                        gps_dt_col = gps_dt_col_,
                        camera_dt_col = camera_dt_col_
                                   )
print(f'First datetime extracted from "{args.gps_csv}" and "{args.img_exif}":')
print(json_dat)
print(f"Addressing offset between camera datetime={json_dat['camera_time']} and gps datetime={json_dat['GPS_time']}...")
offset_ = calc_offset(json_dat, camera_dt_format)
print(f'Offset="{offset_}"')
df_output = resolv_offset(df_img_exif, 
                          camera_dt_col_, 
                          offset_, 
                          new_col = 'updated_datetime')

abs_image_path = os.path.abspath(csv_path)
file_name = os.path.basename(csv_path)
file_name = file_name.split(".csv")[0]
dir_name = "_".join(abs_image_path.split("/")[-2:-1])
out_csv_name = file_name+"_corrected_dt.csv"
df_output.to_csv(out_csv_name, index = False)
print(f'Saved output to: "{out_csv_name}"')
