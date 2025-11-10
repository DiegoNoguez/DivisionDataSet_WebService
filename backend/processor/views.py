import os
import os
os.environ["MPLBACKEND"] = "Agg"
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

import json
import base64
import pandas as pd
import arff
from io import StringIO, BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sklearn.model_selection import train_test_split
import traceback

# ============================================================
# 🔹 CONFIGURACIÓN SEGURA DE MATPLOTLIB PARA ENTORNOS COMO RENDER
# ============================================================
# Evita que Matplotlib intente usar un backend gráfico o cargar fuentes del sistema
os.environ["MPLBACKEND"] = "Agg"

import matplotlib
matplotlib.use("Agg")  # Forzar backend sin GUI
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",  # Fuente interna (no requiere fontconfig)
    "font.sans-serif": ["DejaVu Sans"],
    "figure.max_open_warning": 0,  # Suprime advertencias de figuras abiertas
})

import matplotlib.pyplot as plt


# ============================================================
# 🔹 VISTA PRINCIPAL DE PROCESAMIENTO
# ============================================================
@csrf_exempt
def process_dataset(request):
    if request.method == 'POST':
        try:
            print("Procesando solicitud...")

            # Verificar que se haya enviado un archivo
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'No se envió ningún archivo'}, status=400)

            file = request.FILES['file']
            print(f"Archivo recibido: {file.name}")

            # Leer el contenido del archivo
            content = file.read().decode('utf-8')
            print("Archivo leído correctamente")

            # Cargar dataset
            df = load_kdd_dataset_from_content(content)
            print(f"Dataset cargado: {df.shape}")

            # Realizar divisiones
            train_set, val_set, test_set = train_val_test_split(df, stratify='protocol_type')
            print("Divisiones realizadas")

            # Generar resultados
            results = {
                'dataset_info': get_dataset_info(df),
                'split_sizes': {
                    'train': len(train_set),
                    'validation': len(val_set),
                    'test': len(test_set)
                },
                'protocol_type_distribution': {
                    'original': df['protocol_type'].value_counts().to_dict(),
                    'train': train_set['protocol_type'].value_counts().to_dict(),
                    'validation': val_set['protocol_type'].value_counts().to_dict(),
                    'test': test_set['protocol_type'].value_counts().to_dict()
                },
                'histograms': generate_histograms(df, train_set, val_set, test_set)
            }

            print("Procesamiento completado exitosamente")
            return JsonResponse(results)

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Error durante el procesamiento: {str(e)}")
            print(f"Traceback: {error_trace}")
            return JsonResponse({
                'error': str(e),
                'traceback': error_trace
            }, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================================
# 🔹 FUNCIONES AUXILIARES
# ============================================================

def load_kdd_dataset_from_content(content):
    """Cargar dataset desde contenido en memoria (formato ARFF)."""
    try:
        dataset = arff.loads(content)
        attributes = [attr[0] for attr in dataset['attributes']]
        return pd.DataFrame(dataset['data'], columns=attributes)
    except Exception as e:
        raise Exception(f"Error cargando dataset ARFF: {str(e)}")


def train_val_test_split(df, rstate=42, shuffle=True, stratify=None):
    """Dividir el dataset en train, validation y test sets."""
    try:
        strat = df[stratify] if stratify else None
        train_set, test_set = train_test_split(
            df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat)

        strat = test_set[stratify] if stratify else None
        val_set, test_set = train_test_split(
            test_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat)

        return train_set, val_set, test_set
    except Exception as e:
        raise Exception(f"Error en la división del dataset: {str(e)}")


def get_dataset_info(df):
    """Obtener información general del dataset."""
    try:
        buffer = StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()

        return {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'info_string': info_str,
            'description': df.describe().to_dict()
        }
    except Exception as e:
        raise Exception(f"Error obteniendo información del dataset: {str(e)}")


# ============================================================
# 🔹 GENERACIÓN DE HISTOGRAMAS SEGURA PARA RENDER
# ============================================================
def generate_histograms(df, train_set, val_set, test_set):
    """Generar histogramas y convertirlos a base64."""
    try:
        histograms = {}

        # Dataset original
        plt.figure(figsize=(10, 6))
        df['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Distribución de protocol_type - Dataset Original')
        plt.xlabel('Protocol Type')
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['original'] = plot_to_base64(plt)
        plt.close('all')

        # Training set
        plt.figure(figsize=(10, 6))
        train_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Distribución de protocol_type - Training Set')
        plt.xlabel('Protocol Type')
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['train'] = plot_to_base64(plt)
        plt.close('all')

        # Validation set
        plt.figure(figsize=(10, 6))
        val_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Distribución de protocol_type - Validation Set')
        plt.xlabel('Protocol Type')
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['validation'] = plot_to_base64(plt)
        plt.close('all')

        # Test set
        plt.figure(figsize=(10, 6))
        test_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Distribución de protocol_type - Test Set')
        plt.xlabel('Protocol Type')
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['test'] = plot_to_base64(plt)
        plt.close('all')

        return histograms
    except Exception as e:
        raise Exception(f"Error generando histogramas: {str(e)}")


def plot_to_base64(plt):
    """Convertir un gráfico de Matplotlib a cadena base64 (PNG)."""
    try:
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.clf()  # Limpia figura actual
        return base64.b64encode(image_png).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error convirtiendo plot a base64: {str(e)}")
