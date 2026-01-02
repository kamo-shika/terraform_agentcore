#!/bin/bash

# Lambda デプロイメントパッケージを依存関係と共にビルドするスクリプト

set -e

BUILD_DIR="lambda_build"
LAMBDA_DIR="lambda"

# 前回のビルドをクリーンアップ
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# uv を使用して依存関係をインストール
echo "Installing dependencies..."
uv pip install -r "$LAMBDA_DIR/requirements.txt" --target "$BUILD_DIR" --python-version 3.12

# Lambda 関数コードをコピー
echo "Copying Lambda code..."
cp "$LAMBDA_DIR"/*.py "$BUILD_DIR/"

# デプロイメントパッケージを作成
echo "Creating deployment package..."
cd "$BUILD_DIR"
zip -r ../lambda_function_payload.zip . -q
cd ..

echo "Lambda deployment package created: lambda_function_payload.zip"

# ビルドディレクトリをクリーンアップ
rm -rf "$BUILD_DIR"
rm lambda_function_payload.zip

echo "Build complete."
