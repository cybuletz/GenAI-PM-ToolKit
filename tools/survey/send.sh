#!/bin/bash
# Usage: bash tools/survey/run_survey.sh "Survey Title" "email1,email2" "Friday EOD"
python3 tools/survey/survey.py \
  --title "$1" \
  --emails "$2" \
  --questions tools/survey/questions.json \
  --deadline "$3"
