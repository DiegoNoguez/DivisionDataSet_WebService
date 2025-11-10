import json
import os
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

# Configuración para Render
if 'RENDER' in os.environ:
    # Reducir uso de memoria en Render
    import matplotlib
    matplotlib.use('Agg')

def get_memory_usage():
    """Monitorear uso de memoria (útil para debug en Render)"""
    try:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    except:
        return 0  # Fallback si psutil no está disponible

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
            
            # Cargar dataset con métodos robustos
            df = load_kdd_dataset_from_content(content)
            print(f"Dataset cargado: {df.shape}")
            
            # Liberar contenido original
            del content
            gc.collect()
            
            print(f"Memoria después de cargar dataset: {get_memory_usage():.2f} MB")
            
            # Validar que existe la columna para stratify
            if 'protocol_type' not in df.columns:
                # Buscar columnas similares
                protocol_cols = [col for col in df.columns if 'protocol' in col.lower()]
                if protocol_cols:
                    print(f"Usando columna alternativa para stratify: {protocol_cols[0]}")
                    stratify_col = protocol_cols[0]
                else:
                    return JsonResponse({'error': 'El dataset debe contener la columna "protocol_type" para realizar la división estratificada'}, status=400)
            else:
                stratify_col = 'protocol_type'
            
            # Realizar divisiones con manejo de memoria
            train_set, val_set, test_set = train_val_test_split_optimized(df, stratify=stratify_col)
            
            # Liberar dataframe original
            del df
            gc.collect()
            
            print(f"Memoria después de dividir dataset: {get_memory_usage():.2f} MB")
            
            # Generar resultados de forma eficiente
            results = generate_optimized_results(train_set, val_set, test_set, stratify_col)
            
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

@csrf_exempt
def health_check(request):
    """Endpoint de salud para verificar que el backend funciona"""
    return JsonResponse({
        'status': 'success', 
        'message': 'Backend funcionando correctamente',
        'timestamp': '2024-01-01T00:00:00Z'
    })

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

def generate_optimized_results(train_set, val_set, test_set, stratify_col='protocol_type'):
    """Generar resultados optimizados para memoria"""
    
    # Información básica sin cargar datos pesados
    results = {
        'split_sizes': {
            'train': len(train_set),
            'validation': len(val_set),
            'test': len(test_set)
        },
        'protocol_type_distribution': {
            'train': train_set[stratify_col].value_counts().to_dict(),
            'validation': val_set[stratify_col].value_counts().to_dict(),
            'test': test_set[stratify_col].value_counts().to_dict()
        },
        'histograms': generate_optimized_histograms(train_set, val_set, test_set, stratify_col),
        'dataset_info': {
            'total_instances': len(train_set) + len(val_set) + len(test_set),
            'features_count': len(train_set.columns),
            'stratify_column_used': stratify_col
        }
    }
    
    return results

def generate_optimized_histograms(train_set, val_set, test_set, stratify_col='protocol_type'):
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
        train_set[stratify_col].value_counts().plot(kind='bar')
        plt.title(f'Training Set - {stratify_col}')
        plt.xlabel(stratify_col)
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['train'] = plot_to_base64(plt, dpi=dpi)
        plt.close()
        
        # Histograma validation set
        plt.figure(figsize=fig_size, dpi=dpi)
        val_set[stratify_col].value_counts().plot(kind='bar')
        plt.title(f'Validation Set - {stratify_col}')
        plt.xlabel(stratify_col)
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        histograms['validation'] = plot_to_base64(plt, dpi=dpi)
        plt.close()
        
        # Histograma test set
        plt.figure(figsize=fig_size, dpi=dpi)
        test_set[stratify_col].value_counts().plot(kind='bar')
        plt.title(f'Test Set - {stratify_col}')
        plt.xlabel(stratify_col)
        plt.ylabel('Frecuencia')
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
    """Cargar dataset con métodos robustos para NSL-KDD"""
    try:
        # Primero intentar carga normal
        return load_kdd_dataset_normal(content)
    except Exception as e1:
        print(f"=== FALLO CARGA NORMAL: {str(e1)} ===")
        try:
            # Segundo intento: carga permisiva
            return load_kdd_dataset_permissive(content, str(e1))
        except Exception as e2:
            print(f"=== FALLO CARGA PERMISIVA: {str(e2)} ===")
            try:
                # Tercer intento: carga específica NSL-KDD
                return load_nsl_kdd_dataset(content)
            except Exception as e3:
                print(f"=== FALLO TODOS LOS MÉTODOS ===")
                raise Exception(f"No se pudo cargar el archivo ARFF. Errores:\n1. {e1}\n2. {e2}\n3. {e3}")

def load_kdd_dataset_normal(content):
    """Carga normal de ARFF"""
    dataset = arff.loads(content)
    attributes = [attr[0] for attr in dataset['attributes']]
    
    if not dataset['data']:
        raise Exception("El dataset está vacío")
        
    return pd.DataFrame(dataset['data'], columns=attributes)

def load_kdd_dataset_permissive(content, original_error):
    """Cargar dataset NSL-KDD con formato más permisivo"""
    try:
        print("=== INTENTANDO CARGA PERMISIVA ===")
        
        lines = content.split('\n')
        cleaned_lines = []
        
        # Limpiar el archivo línea por línea
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Saltar líneas vacías
            if not line:
                continue
                
            # Manejar atributos problemáticos
            if line.lower().startswith('@attribute'):
                # Corregir problemas comunes en NSL-KDD
                if 'string' in line.lower():
                    line = line.replace('string', 'STRING')
                if 'real' in line.lower():
                    line = line.replace('real', 'NUMERIC')
                if 'integer' in line.lower():
                    line = line.replace('integer', 'NUMERIC')
                
                # Asegurar formato correcto para nominales
                if '{' in line and '}' in line:
                    # Ya es un atributo nominal, dejarlo como está
                    pass
                elif 'protocol_type' in line.lower():
                    line = '@ATTRIBUTE protocol_type {tcp,udp,icmp}'
                elif 'service' in line.lower():
                    line = '@ATTRIBUTE service {http,ftp,smtp,ssh,dns,other}'
                elif 'flag' in line.lower():
                    line = '@ATTRIBUTE flag {SF,S1,S2,S3,S0,OTH}'
                elif 'land' in line.lower():
                    line = '@ATTRIBUTE land {0,1}'
                elif 'logged_in' in line.lower():
                    line = '@ATTRIBUTE logged_in {0,1}'
                elif 'is_host_login' in line.lower():
                    line = '@ATTRIBUTE is_host_login {0,1}'
                elif 'is_guest_login' in line.lower():
                    line = '@ATTRIBUTE is_guest_login {0,1}'
            
            cleaned_lines.append(line)
        
        # Reconstruir contenido limpio
        cleaned_content = '\n'.join(cleaned_lines)
        
        print("=== CONTENIDO LIMPIO (primeras 20 líneas) ===")
        print('\n'.join(cleaned_lines[:20]))
        print("=== FIN CONTENIDO LIMPIO ===")
        
        # Intentar cargar el contenido limpio
        dataset = arff.loads(cleaned_content)
        attributes = [attr[0] for attr in dataset['attributes']]
        
        print(f"=== CARGA PERMISIVA EXITOSA ===")
        print(f"Atributos: {attributes}")
        print(f"Número de instancias: {len(dataset['data'])}")
        
        return pd.DataFrame(dataset['data'], columns=attributes)
        
    except Exception as e:
        print(f"=== FALLA EN CARGA PERMISIVA ===")
        print(f"Error: {str(e)}")
        raise Exception(f"No se pudo cargar el archivo ARFF. Error original: {original_error}. Error en carga permisiva: {str(e)}")

def load_nsl_kdd_dataset(content):
    """Cargar específicamente datasets NSL-KDD"""
    try:
        print("=== INTENTANDO CARGA ESPECÍFICA NSL-KDD ===")
        
        # Saltar directamente a los datos si el header tiene problemas
        lines = content.split('\n')
        
        # Buscar la línea @DATA
        data_start = None
        for i, line in enumerate(lines):
            if line.strip().upper() == '@DATA':
                data_start = i + 1
                break
        
        if data_start is None:
            raise Exception("No se encontró la sección @DATA en el archivo")
        
        # Atributos predefinidos para NSL-KDD (basado en KDDTest+.arff)
        attributes = [
            'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 
            'dst_bytes', 'land', 'wrong_fragment', 'urgent', 'hot',
            'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
            'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
            'num_access_files', 'num_outbound_cmds', 'is_host_login',
            'is_guest_login', 'count', 'srv_count', 'serror_rate',
            'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
            'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count',
            'dst_host_srv_count', 'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
            'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate',
            'dst_host_serror_rate', 'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
            'dst_host_srv_rerror_rate', 'class'
        ]
        
        # Leer los datos
        data_lines = []
        for line in lines[data_start:]:
            line = line.strip()
            if line and not line.startswith('%'):  # Saltar líneas vacías y comentarios
                data_lines.append(line)
        
        # Parsear los datos
        data = []
        for line in data_lines:
            values = line.split(',')
            if len(values) == len(attributes):
                # Convertir valores numéricos
                processed_values = []
                for i, value in enumerate(values):
                    value = value.strip().strip("'\"")  # Remover comillas
                    if value.replace('.', '').replace('-', '').isdigit():
                        try:
                            if '.' in value:
                                processed_values.append(float(value))
                            else:
                                processed_values.append(int(value))
                        except:
                            processed_values.append(value)
                    else:
                        processed_values.append(value)
                data.append(processed_values)
        
        if not data:
            raise Exception("No se pudieron cargar datos del archivo")
        
        print(f"=== CARGA NSL-KDD EXITOSA ===")
        print(f"Instancias cargadas: {len(data)}")
        print(f"Atributos: {len(attributes)}")
        
        return pd.DataFrame(data, columns=attributes)
        
    except Exception as e:
        raise Exception(f"Error cargando dataset NSL-KDD: {str(e)}")

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