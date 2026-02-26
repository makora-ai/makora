#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

mkdir -p "$SCRIPT_DIR/../data/"
curl -o $SCRIPT_DIR/../data/openapi.json https://generate.stage.makora.com/api/v1/openapi.json

datamodel-codegen \
    --input $SCRIPT_DIR/../data/openapi.json \
    --input-file-type openapi \
    --output $SCRIPT_DIR/../makora/models/openapi.py \
    --output-model-type pydantic_v2.BaseModel \
    --output-datetime-class datetime

echo "client generated successfully"
