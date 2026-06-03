import pandas as pd
import numpy as np
import os

def create_gold_layer():
    print("⏳ Generando Data Lake mock en formato Parquet...")
    
    # Simulamos 100,000 registros históricos de tráfico
    np.random.seed(42)
    n_records = 100000
    
    df = pd.DataFrame({
        'route_id': np.random.choice(['R-101', 'R-102', 'R-103'], n_records),
        'latitude': np.random.uniform(-16.5, -16.6, n_records), # Coordenadas base
        'longitude': np.random.uniform(-68.1, -68.2, n_records),
        'historical_avg_speed': np.random.normal(25, 10, n_records), # Vel. promedio
        'congestion_probability': np.random.uniform(0, 1, n_records)
    })
    
    os.makedirs('data', exist_ok=True)
    file_path = 'data/mock_historical_data.parquet'
    
    # Guardamos en formato columnar (Parquet), ideal para compresión y analítica
    df.to_parquet(file_path, engine='pyarrow', index=False)
    print(f"✅ Archivo Parquet creado exitosamente en: {file_path}")

if __name__ == "__main__":
    create_gold_layer()