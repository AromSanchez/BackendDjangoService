#!/usr/bin/env python
"""
Script para verificar la conexión a Redis
"""
import redis
import sys

def check_redis():
    try:
        # Conectar a Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Hacer ping
        response = r.ping()
        
        if response:
            print("✅ Redis está corriendo y accesible")
            print(f"📊 Información de Redis:")
            info = r.info()
            print(f"   - Versión: {info.get('redis_version', 'N/A')}")
            print(f"   - Modo: {info.get('redis_mode', 'N/A')}")
            print(f"   - Clientes conectados: {info.get('connected_clients', 'N/A')}")
            return True
        else:
            print("❌ Redis no responde al ping")
            return False
            
    except redis.ConnectionError:
        print("❌ No se puede conectar a Redis")
        print("💡 Asegúrate de que Redis esté instalado y corriendo en localhost:6379")
        print("   - Windows: Descargar Redis desde https://github.com/microsoftarchive/redis/releases")
        print("   - O usar Docker: docker run -d -p 6379:6379 redis:alpine")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Verificando conexión a Redis...")
    
    if check_redis():
        print("\n🎉 Redis está listo para Django Channels!")
        sys.exit(0)
    else:
        print("\n⚠️  Redis no está disponible. WebSocket no funcionará sin Redis.")
        sys.exit(1)
