import json
import base64
import pandas as pd
import arff
from io import StringIO, BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo - CRUCIAL para Render
import matplotlib.pyplot as plt
import traceback
import gc  # Garbage collector para liberar memoria
import psutil  # Para monitorear memoria (opcional)

def get_memory_usage():
    """Monitorear uso de memoria (útil para debug en Render)"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB

@csrf_exempt
def process_dataset(request):
    if request.method == 'POST':
        try:
            print(f"Memoria inicial: {get_memory_usage():.2f} MB")
            
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'No se envió ningún archivo'}, status=400)
            
            file = request.FILES['file']
            
            # Validar tamaño del archivo (máximo 10MB para plan gratuito)
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'El archivo es demasiado grande. Máximo 10MB.'}, status=400)
            
            print(f"Procesando archivo: {file.name} ({file.size / 1024 / 1024:.2f} MB)")
            
            # Leer y procesar en chunks si es necesario
            content = file.read().decode('utf-8')
            
            # Liberar memoria del archivo inmediatamente
            del file
            gc.collect()
            
            print(f"Memoria después de leer archivo: {get_memory_usage():.2f} MB")
            
            # Cargar dataset
            df = load_kdd_dataset_from_content(content)
            print(f"Dataset cargado: {df.shape}")
            
            # Liberar contenido original
            del content
            gc.collect()
            
            print(f"Memoria después de cargar dataset: {get_memory_usage():.2f} MB")
            
            # Validar que existe la columna para stratify
            if 'protocol_type' not in df.columns:
                return JsonResponse({'error': 'El dataset debe contener la columna "protocol_type"'}, status=400)
            
            # Realizar divisiones con manejo de memoria
            train_set, val_set, test_set = train_val_test_split_optimized(df, stratify='protocol_type')
            
            # Liberar dataframe original
            del df
            gc.collect()
            
            print(f"Memoria después de dividir dataset: {get_memory_usage():.2f} MB")
            
            # Generar resultados de forma eficiente
            results = generate_optimized_results(train_set, val_set, test_set)
            
            # Liberar datasets divididos
            del train_set, val_set, test_set
            gc.collect()
            
            print(f"Memoria final: {get_memory_usage():.2f} MB")
            print("Procesamiento completado exitosamente")
            
            return JsonResponse(results)
            
        except MemoryError:
            error_msg = "Error de memoria: El dataset es demasiado grande para procesar en el plan gratuito."
            print(error_msg)
            return JsonResponse({'error': error_msg}, status=400)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Error durante el procesamiento: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'traceback': error_trace
            }, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def train_val_test_split_optimized(df, rstate=42, shuffle=True, stratify=None):
    """División optimizada para memoria"""
    strat = df[stratify] if stratify else None
    
    # Usar índices en lugar de copiar datos cuando sea posible
    train_set, test_set = train_test_split(
        df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat)

    strat = test_set[stratify] if stratify else None
    val_set, test_set = train_test_split(
        test_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat)
    
    return train_set, val_set, test_set

def generate_optimized_results(train_set, val_set, test_set):
    """Generar resultados optimizados para memoria"""
    
    # Información básica sin cargar datos pesados
    results = {
        'split_sizes': {
            'train': len(train_set),
            'validation': len(val_set),
            'test': len(test_set)
        },
        'protocol_type_distribution': {
            'train': train_set['protocol_type'].value_counts().to_dict(),
            'validation': val_set['protocol_type'].value_counts().to_dict(),
            'test': test_set['protocol_type'].value_counts().to_dict()
        },
        'histograms': generate_optimized_histograms(train_set, val_set, test_set)
    }
    
    return results

def generate_optimized_histograms(train_set, val_set, test_set):
    """Generar histogramas optimizados"""
    histograms = {}
    
    # Configuración mínima de matplotlib
    plt.switch_backend('Agg')
    
    # Tamaño reducido de figuras para ahorrar memoria
    fig_size = (8, 4)
    dpi = 80  # Reducir DPI para imágenes más pequeñas
    
    try:
        # Histograma training set
        plt.figure(figsize=fig_size, dpi=dpi)
        train_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Training Set - Protocol Type')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['train'] = plot_to_base64(plt, dpi=dpi)
        plt.close()
        
        # Histograma validation set
        plt.figure(figsize=fig_size, dpi=dpi)
        val_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Validation Set - Protocol Type')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['validation'] = plot_to_base64(plt, dpi=dpi)
        plt.close()
        
        # Histograma test set
        plt.figure(figsize=fig_size, dpi=dpi)
        test_set['protocol_type'].value_counts().plot(kind='bar')
        plt.title('Test Set - Protocol Type')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['test'] = plot_to_base64(plt, dpi=dpi)
        plt.close()
        
    except Exception as e:
        print(f"Error generando histogramas: {str(e)}")
        # Devolver histogramas vacíos en caso de error
        histograms = {
            'train': '',
            'validation': '', 
            'test': ''
        }
    
    return histograms

def load_kdd_dataset_from_content(content):
    """Cargar dataset optimizado"""
    try:
        dataset = arff.loads(content)
        attributes = [attr[0] for attr in dataset['attributes']]
        return pd.DataFrame(dataset['data'], columns=attributes)
    except Exception as e:
        raise Exception(f"Error cargando dataset ARFF: {str(e)}")

def plot_to_base64(plt, dpi=80):
    """Convertir plot a base64 optimizado"""
    try:
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=dpi, 
                   optimize=True, metadata={'Software': ''})  # Optimizar PNG
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        return base64.b64encode(image_png).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error convirtiendo plot a base64: {str(e)}")