"""
Script para verificar las tablas creadas en la base de datos
"""
import pymysql

# Configuración de conexión (debe coincidir con settings.py)
connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='conecta_ya',
    port=3306
)

try:
    with connection.cursor() as cursor:
        # Obtener todas las tablas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("=" * 60)
        print("TABLAS EN LA BASE DE DATOS 'conecta_ya'")
        print("=" * 60)
        
        django_tables = []
        springboot_tables = []
        
        for table in tables:
            table_name = table[0]
            
            # Clasificar tablas
            if table_name in ['user_profiles', 'categories', 'services', 'service_images', 
                             'bookings', 'reviews', 'favorites', 'reports', 
                             'conversations', 'conversation_participants', 'messages']:
                django_tables.append(table_name)
            elif table_name in ['users', 'password_reset_tokens', 'identity_documents', 
                               'files', 'user_reputation', 'notifications', 'system_settings']:
                springboot_tables.append(table_name)
        
        print("\n🟩 TABLAS DE DJANGO:")
        for table in sorted(django_tables):
            print(f"  ✅ {table}")
        
        print(f"\nTotal Django: {len(django_tables)} tablas")
        
        print("\n🟦 TABLAS DE SPRING BOOT:")
        for table in sorted(springboot_tables):
            print(f"  ✅ {table}")
        
        print(f"\nTotal Spring Boot: {len(springboot_tables)} tablas")
        
        print("\n📊 OTRAS TABLAS:")
        other_tables = [t[0] for t in tables if t[0] not in django_tables and t[0] not in springboot_tables]
        for table in sorted(other_tables):
            print(f"  • {table}")
        
        print(f"\nTotal Otras: {len(other_tables)} tablas")
        print(f"\n🎯 TOTAL GENERAL: {len(tables)} tablas")
        print("=" * 60)
        
        # Verificar estructura de una tabla de ejemplo
        print("\n📋 ESTRUCTURA DE LA TABLA 'services':")
        cursor.execute("DESCRIBE services")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  • {col[0]}: {col[1]}")

finally:
    connection.close()
