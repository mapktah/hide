#!/usr/bin/env bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"
exit 0
########################################################################################
# Modify only these variables
########################################################################################
# Where this script is relative to project directory
PYTHON_VER="3.6"
MODULE_TO_RUN=""
# Folders separated by ":"
EXTERNAL_SRC_FOLDERS=""
########################################################################################

PYTHON_BIN=""
FOUND=0
#
# Look for possible python paths
#
for path in "/usr/bin/python$PYTHON_VER" "/usr/local/bin/python$PYTHON_VER"; do
    echo "[$SCRIPT_NAME] Checking python path $path.."

    if ls $path 2>/dev/null 1>/dev/null; then
        echo "[$SCRIPT_NAME]   OK Found python path in $path"
        PYTHON_BIN=$path
        FOUND=1
        break
    else
        echo "[$SCRIPT_NAME]   ERROR No python in path $path"
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "[$SCRIPT_NAME]   ERROR No python binary found!!"
    exit 1
fi

export PYTHONIOENCODING=utf-8

# Cleanup log files older 7 days = 604800 secs
PYTHONPATH="$EXTERNAL_SRC_FOLDERS" \
   $PYTHON_BIN -m "$MODULE_TO_RUN" \
     folder="../app.data/server" \
     regex="(.outerr)|(.log)" \
     maxage=604800
