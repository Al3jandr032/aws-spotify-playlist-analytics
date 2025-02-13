import boto3
import pandas as pd
import json
from io import BytesIO
import os

# Configuración
BUCKET_NAME = "spoti-reports-data"
RAW_PREFIX = "raw/"
CURATED_PREFIX = "curated/"

# Inicializar cliente S3
s3 = boto3.client('s3')

# Obtener el archivo JSON más reciente
response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=RAW_PREFIX)
latest_file = max(response.get('Contents', []), key=lambda x: x['LastModified'])
file_key = latest_file['Key']

# Leer el archivo JSON desde S3
obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
data = json.load(obj['Body'])

# Transformar datos con Pandas
tracks = []
for item in data['items']:
    track = item['track']
    tracks.append({
        "song_name": track['name'],
        "artist_name": track['artists'][0]['name'],
        "duration_min": track['duration_ms'] / 60000,
        "added_date": item['added_at']
    })

df = pd.DataFrame(tracks)

# Guardar como archivo Parquet
parquet_buffer = BytesIO()
df.to_parquet(parquet_buffer, index=False)

# Subir el archivo Parquet a S3
output_key = f"{CURATED_PREFIX}{os.path.basename(file_key).replace('.json', '.parquet')}"
s3.put_object(Bucket=BUCKET_NAME, Key=output_key, Body=parquet_buffer.getvalue())

print(f"Archivo Parquet guardado en {output_key}")
