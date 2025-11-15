#!/usr/bin/env python
"""
Script para ejecutar Django con soporte WebSocket usando Daphne
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectaya.settings')
    
    # Configurar Django
    django.setup()
    
    # Ejecutar con Daphne para soporte WebSocket
    print("🚀 Iniciando Django con soporte WebSocket...")
    print("📡 WebSocket URL: ws://localhost:8000/ws/chat/")
    print("🌐 HTTP URL: http://localhost:8000/")
    
    # Ejecutar Daphne
    import subprocess
    import os
    
    # Cambiar al directorio del proyecto
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Ejecutar daphne directamente
    subprocess.run([
        'python', '-m', 'daphne',
        '-b', '0.0.0.0',
        '-p', '8000',
        'conectaya.asgi:application'
    ])
