#!/bin/bash

virtualenv --python=python3.10 "myenv"
source "myenv/bin/activate"
pip install --upgrade pip
#pip install pip-tools
#pip-compile --output-file requirements.txt.lock requirements.txt
pip install -r requirements.txt.lock
