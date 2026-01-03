#!/bin/bash

# Lambda デプロイメントパッケージを依存関係と共にビルドするスクリプト

set -eu

# プロジェクトと一致するPythonバージョン
PYTHON_VERSION="3.13"
BUILD_DIR="lambda_build"
LAMBDA_DIR="lambda"
OUTPUT_ZIP="lambda_function_payload.zip"

# 前回のビルドをクリーンアップ
echo "Cleaning up previous build..."
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_ZIP"
mkdir -p "$BUILD_DIR"

# Lambda ディレクトリの存在確認
if [ ! -d "$LAMBDA_DIR" ]; then
    echo "Error: Lambda directory '$LAMBDA_DIR' does not exist"
    exit 1
fi

if [ ! -f "$LAMBDA_DIR/requirements.txt" ]; then
    echo "Error: requirements.txt not found in '$LAMBDA_DIR'"
    exit 1
fi

# uv を使用して依存関係をインストール
echo "Installing dependencies (Python $PYTHON_VERSION)..."
uv pip install -r "$LAMBDA_DIR/requirements.txt" --target "$BUILD_DIR" --python-version "$PYTHON_VERSION"

# Lambda 関数コードをコピー
echo "Copying Lambda code..."
cp "$LAMBDA_DIR"/*.py "$BUILD_DIR/"

# デプロイメントパッケージを作成
echo "Creating deployment package..."
cd "$BUILD_DIR"
zip -r "../$OUTPUT_ZIP" . -q
cd ..

# ZIP作成の検証
if [ ! -f "$OUTPUT_ZIP" ]; then
    echo "Error: Failed to create deployment package"
    exit 1
fi

ZIP_SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)
echo "Lambda deployment package created: $OUTPUT_ZIP ($ZIP_SIZE)"

# ZIPの中身を確認（簡易検証）
ZIP_FILE_COUNT=$(unzip -l "$OUTPUT_ZIP" | tail -1 | awk '{print $2}')
echo "Package contains $ZIP_FILE_COUNT files"

# ビルドディレクトリをクリーンアップ
rm -rf "$BUILD_DIR"
# 注意: lambda_function_payload.zipはTerraformで必要なため削除しない

echo "Build complete."
