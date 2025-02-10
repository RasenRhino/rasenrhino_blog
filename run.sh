#!/bin/bash 
rm -rf build
python parser.py
python -m http.server --directory build

