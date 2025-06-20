#!/bin/bash
set -e # exit when non-zero exit status
usage(){
	echo "Usage: $(basename "$0") -g <.csv file path> -i <directory>"
	echo "             where command is one of the following: "
	echo "                   g (gps_csv)                  - parsed gps csv log file---output of parse_gpslog_and_reformat.py"
	echo "                   i (image_dir)                - Enter path to camera image files"
    echo "Please note that this script depends on the following:"
    echo " 1. exiftool"
    echo " 2. geotagre.py"
    echo " 3. reconsile_offset_v3.py"
    echo " 4. match_datetime_v3.py"
   	exit 1

}

while getopts ":h:g:i:" opt; do
	case "$opt" in 
		h)
			usage
			exit 1
			;;

		g) GPS_LOG=$OPTARG ;;
		i) IMG_DIR=$OPTARG ;;
		\\?) echo "invalid option has been entered: $OPTARG" >&2; exit1 ;;
	esac
done

if [[ -z $GPS_LOG || -z $IMG_DIR ]]; then
    echo "Error: both -i (image_dir) and -g (gps_csv) are mendatory arguments."; 
    usage ;
    exit 1;
fi

echo "** gps_csv: $GPS_LOG"
echo "** image_path: $IMG_DIR"
IMG_DIR_ABS=$(realpath ${IMG_DIR})
IMG_DIR_BASE=$(basename ${IMG_DIR_ABS})
IMG_DIR_DIR=$(basename $(dirname ${IMG_DIR_ABS}))
echo "$IMG_DIR_ABS"
echo "$IMG_DIR_DIR"
OUT_NAME="${IMG_DIR_DIR}_${IMG_DIR_BASE}"
OUT_IMG_EXIF=${OUT_NAME}_exif.csv
echo "** image exif output: $OUT_IMG_EXIF"

printf "\n*******\n"
echo "Processing all images within $IMG_DIR..."
exiftool -DateTimeOriginal -csv -c "%%.6f" $IMG_DIR/*.JPG > $OUT_IMG_EXIF

printf "\n*******\n"
echo "Correcting datetime offsets in image exif..."
python reconsile_offset_v3.py -gps $GPS_LOG -exif $OUT_IMG_EXIF
echo "Done."

printf "\n*******\n"
## simple matching method, including dynamic time wrapping.
echo "Matching camera datetime to GPS datetime for geotagging..."
python match_datetime_v3.py -gps $GPS_LOG -exif ${OUT_NAME}_exif_corrected_dt.csv -n 8 -o ${OUT_NAME}_MATCHED.csv
echo "Done. Check if geotagging went well in $IMG_DIR. e.g., exiftool -GPS* -Date* [image_name.jpg]"