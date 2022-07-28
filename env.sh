#!/bin/sh

# NOTICE: YOU NEED TO RUN THIS FILE WITH `source env.sh`


source /user/work/gh18931/diss/smalst_custom/venv_smalst/bin/activate
#module load libs/cudnn/10.1-cuda-10.0
#module load build/gcc-7.2.0
#or 
#module load languages/anaconda3/2021-3.8.8-cuda-11.1-pytorch

# this is forcing neural_render's main code into the python import search path
# so when you load env it won't explode for some dumb importerror
export PYTHONPATH="$(realpath smalst/external/neural_renderer/neural_renderer)"