#!/bin/sh

find . -name "*.zip" -type f -delete
find . -name "*.pyo" -type f -delete
find . -name "*.pyc" -type f -delete
python addons_zip_generator.py
python addons_xml_generator.py