#!/bin/bash

# Build script for Lambda deployment package with dependencies

set -e

BUILD_DIR="lambda_build"
LAMBDA_DIR="lambda"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install dependencies using uv
echo "Installing dependencies..."
uv pip install -r "$LAMBDA_DIR/requirements.txt" --target "$BUILD_DIR" --python-version 3.12

# Copy Lambda function code
echo "Copying Lambda code..."
cp "$LAMBDA_DIR"/*.py "$BUILD_DIR/"

# Create deployment package
echo "Creating deployment package..."
cd "$BUILD_DIR"
zip -r ../lambda_function_payload.zip . -q
cd ..

echo "Lambda deployment package created: lambda_function_payload.zip"

# Clean up build directory
rm -rf "$BUILD_DIR"
rm lambda_function_payload.zip

echo "Build complete."
