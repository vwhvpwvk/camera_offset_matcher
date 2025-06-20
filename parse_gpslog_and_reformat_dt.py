
import argparse
import pandas as pd
import datetime
import os
import glob
from geotagre import parse_gps_log, epoch_ms_to_datetime
    
parser = argparse.ArgumentParser(description="this is a code to get datetime from unix epoch.")

parser.add_argument("-f", "--filename", 
                    type=str, 
                    help="The name of the file to process",
                    required=True) 

parser.add_argument("-l", "--line_begins", 
                    type=int, 
                    help="Specify line number that the script reads. The script removes every line before the specified line number.",
                    required=True) 

parser.add_argument("-tc", "--target_column",
                    type = str,
                    help = 'column name of datetime data with epoch ms',
                    default = 'timestamp')

args = parser.parse_args()

target_col = args.target_column
filename = args.filename
basename = os.path.basename(filename).split(".")[0]
dirname  = os.path.dirname(filename)

df= parse_gps_log(filename, args.line_begins) #pd.read_csv(filename)
print(df.columns)
print(df.head)

df['datetime'] = [epoch_ms_to_datetime(item).strftime("%Y-%m-%d %H:%M:%S.%f") for item in df[target_col]]
current_time = datetime.datetime.now()
yymmdd = current_time.strftime("%y%m%d")
out_csvname = f"{basename}_cleaned_{yymmdd}.csv"
out_filename = os.path.join(dirname, out_csvname)
print(f"updated {filename} with date time, to {out_filename}")
df.to_csv(out_filename, index=False)
