"""
Скрипт для скачивания и распаковки модели Vosk (пример: русский язык, small-версия).
"""
import os
import zipfile
import requests
from pathlib import Path

VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
TARGET_DIR = "models/asr/vosk/"
MODEL_ZIP_NAME = "vosk-model-small-ru-0.22.zip"


def download_file(url, filepath):
    resp = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def unzip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    zip_path = os.path.join(TARGET_DIR, MODEL_ZIP_NAME)
    print(f"Downloading model from {VOSK_MODEL_URL} ...")
    if not Path(zip_path).exists():
        download_file(VOSK_MODEL_URL, zip_path)
        print("Downloaded!")
    else:
        print("Archive already exists.")
    print("Unzipping ...")
    unzip_file(zip_path, TARGET_DIR)
    print("Done! Model is available at:")
    print(os.path.join(TARGET_DIR, 'vosk-model-small-ru-0.22'))

if __name__ == "__main__":
    main()

