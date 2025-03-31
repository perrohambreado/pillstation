from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    User, Administrador, Enfermero, 
    EnfermeroMongo, MongoAdministrador, 
    EnfermeroPastillero, Pastillero, Medicamento
)

@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    
    if hasattr(instance, '_skip_signal') and instance._skip_signal:
        return
    
    print(f"DEBUG - Usuario guardado: {instance.username}, tipo: {instance.tipo_usuario}")
    
    with transaction.atomic():
        if instance.tipo_usuario == 'admin':
            if hasattr(instance, 'enfermero'):
                sync_admin_to_mongo(instance.admin)
        elif instance.tipo_usuario == 'enfermero':
            if hasattr(instance, 'enfermero'):
                sync_nurse_to_mongo(instance.enfermero)

@receiver(post_save, sender=Administrador)
def handle_admin_save(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    with transaction.atomic():
        sync_admin_to_mongo(instance)

@receiver(post_save, sender=Enfermero)
def handle_nurse_save(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    with transaction.atomic():
        sync_nurse_to_mongo(instance)

@receiver(post_save, sender=EnfermeroPastillero)
def handle_pastillero_relation(sender, instance, created, **kwargs):
    try:
        pastilleros = list(EnfermeroPastillero.objects.filter(
            enfermero=instance.enfermero
        ).values_list('pastillero_id', flat=True))

        # Usar mongoengine correctamente
        enfermero_mongo = EnfermeroMongo.objects(usuario_id=instance.enfermero.usuario.id).first()
        if enfermero_mongo:
            enfermero_mongo.pastilleros_autorizados = pastilleros
            enfermero_mongo.save()
            print(f"✅ Relación pastillero actualizada para enfermero {instance.enfermero.usuario.username}")
        else:
            print(f"❌ No se encontró el enfermero en MongoDB con ID {instance.enfermero.usuario.id}")
    except Exception as e:
        print(f"❌ Error al sincronizar relación pastillero: {e}")
        # Para desarrollo, es útil ver el error completo
        import traceback
        traceback.print_exc()

def sync_pastillero_relation(enfermero_id, pastillero_id, add=True):
    from django.db import transaction
    
    try:
        with transaction.atomic():
            enfermero = Enfermero.objects.get(id=enfermero_id)
            
            if add:
                EnfermeroPastillero.objects.get_or_create(
                    enfermero=enfermero, 
                    pastillero_id=pastillero_id
                )
            else:
                EnfermeroPastillero.objects.filter(
                    enfermero=enfermero,
                    pastillero_id=pastillero_id
                ).delete()
                
            enfermero_mongo = EnfermeroMongo.objects(usuario_id=enfermero.usuario.id).first()
            if not enfermero_mongo:
                raise ValueError(f"No se encontró el enfermero en MongoDB: {enfermero.usuario.id}")
                
            pastillero = Pastillero.objects(id=pastillero_id).first()
            if not pastillero:
                raise ValueError(f"No se encontró el pastillero en MongoDB: {pastillero_id}")
            
            if add:
                enfermeros_ids = [str(ref.id) for ref in pastillero.enfermeros_autorizados]
                if str(enfermero_mongo.id) not in enfermeros_ids:
                    pastillero.enfermeros_autorizados.append(enfermero_mongo)
                    pastillero.save()
            else:
                pastillero.enfermeros_autorizados = [
                    ref for ref in pastillero.enfermeros_autorizados 
                    if str(ref.id) != str(enfermero_mongo.id)
                ]
                pastillero.save()
                
            return True
    except Exception as e:
        print(f"Error al sincronizar relación pastillero-enfermero: {e}")
        import traceback
        traceback.print_exc()
        return False

def sync_admin_to_mongo(admin_instance):
    usuario = admin_instance.usuario

    admin_data = {
        'usuario_id': usuario.id,  # Aseguramos que el ID se establece correctamente
        'username': usuario.username,
        'email': usuario.email,
        'password': usuario.password, 
        'is_active': usuario.is_active,
        'fecha_registro': usuario.date_joined,
        'departamento': admin_instance.departamento,
        'nivel_acceso': admin_instance.nivel_acceso,
        'telefono': usuario.telefono,
    }

    try:
        # Buscar si el administrador ya existe
        admin_mongo = MongoAdministrador.objects(usuario_id=usuario.id).first()
        if admin_mongo is None:
            # Si no existe, creamos uno nuevo
            admin_mongo = MongoAdministrador(**admin_data)
            admin_mongo.save()
            print(f"✅ Administrador {usuario.username} creado en MongoDB")
        else:
            # Si ya existe, actualizamos los campos
            for key, value in admin_data.items():
                setattr(admin_mongo, key, value)
            admin_mongo.save()
            print(f"✅ Administrador {usuario.username} actualizado en MongoDB")
    except Exception as e:
        print(f"❌ Error al sincronizar administrador con MongoDB: {e}")
        # Para desarrollo, es útil ver el error completo
        import traceback
        traceback.print_exc()


def eliminar_admin_de_mongo(usuario_id):
    try:
        admin_mongo = MongoAdministrador.objects(usuario_id=usuario_id).first()
        if admin_mongo:
            admin_mongo.delete()
            print(f"✅ Administrador eliminado en MongoDB (ID: {usuario_id})")
        else:
            print(f"⚠️ No se encontró el administrador en MongoDB (ID: {usuario_id})")
    except Exception as e:
        print(f"❌ Error al eliminar administrador en MongoDB: {e}")
        import traceback
        traceback.print_exc()


def eliminar_enfermero_de_mongo(usuario_id):
    try:
        enfermero_mongo = EnfermeroMongo.objects(usuario_id=usuario_id).first()
        if enfermero_mongo:
            enfermero_mongo.delete()
            print(f"✅ Enfermero eliminado en MongoDB (ID: {usuario_id})")
        else:
            print(f"⚠️ No se encontró el enfermero en MongoDB (ID: {usuario_id})")
    except Exception as e:
        print(f"❌ Error al eliminar enfermero en MongoDB: {e}")
        import traceback
        traceback.print_exc()


def sync_nurse_to_mongo(nurse_instance):
    usuario = nurse_instance.usuario
    
    pastilleros = list(EnfermeroPastillero.objects.filter(
        enfermero=nurse_instance
    ).values_list('pastillero_id', flat=True))
    
    nurse_data = {
        'usuario_id': usuario.id,
        'username': usuario.username,
        'email': usuario.email,
        'nombre': nurse_instance.nombre,
        'apellidos': nurse_instance.apellidos,
        'nfc_id': nurse_instance.nfc_id,
        'turno': nurse_instance.turno,
        'activo': nurse_instance.activo,
        'fecha_registro': nurse_instance.fecha_registro or timezone.now(),
        'estatus': nurse_instance.estatus,
        'telefono_cel': nurse_instance.telefono_cel,
        'pastilleros_autorizados': pastilleros,
    }

    try:
        # Verificamos explícitamente que estamos usando la clase correcta
        print(f"Intentando sincronizar enfermero {usuario.username} con MongoDB")
        print(f"Buscando en la colección: {EnfermeroMongo._meta['collection']}")
        
        # Usar la API de mongoengine para interactuar con MongoDB
        enfermero_mongo = EnfermeroMongo.objects(usuario_id=usuario.id).first()
        
        if enfermero_mongo is None:
            # Si no existe, creamos uno nuevo
            print(f"Creando nuevo documento en colección {EnfermeroMongo._meta['collection']}")
            enfermero_mongo = EnfermeroMongo(**nurse_data)
            enfermero_mongo.save()
            print(f"✅ Enfermero {usuario.username} creado en MongoDB")
        else:
            # Si ya existe, actualizamos los campos
            print(f"Actualizando documento existente en colección {EnfermeroMongo._meta['collection']}")
            for key, value in nurse_data.items():
                setattr(enfermero_mongo, key, value)
            enfermero_mongo.save()
            print(f"✅ Enfermero {usuario.username} actualizado en MongoDB")
    except Exception as e:
        print(f"❌ Error al sincronizar enfermero con MongoDB: {e}")
        # Para desarrollo, es útil ver el error completo
        import traceback
        traceback.print_exc()

# Función de utilidad para verificar la sincronización
def verify_mongo_sync():
    """
    Verifica que todos los usuarios en SQLite estén correctamente sincronizados en MongoDB.
    Útil para diagnóstico y para sincronizar datos existentes.
    """
    print("=== Verificando sincronización con MongoDB ===")
    
    # Verificar administradores
    admins = Administrador.objects.all()
    print(f"Total de administradores en SQLite: {admins.count()}")
    
    for admin in admins:
        try:
            admin_mongo = MongoAdministrador.objects(usuario_id=admin.usuario.id).first()
            if admin_mongo:
                print(f"✅ Administrador {admin.usuario.username} existe en MongoDB")
            else:
                print(f"❌ Administrador {admin.usuario.username} NO existe en MongoDB - sincronizando...")
                sync_admin_to_mongo(admin)
        except Exception as e:
            print(f"❌ Error al verificar administrador {admin.usuario.username}: {e}")
    
    # Verificar enfermeros
    enfermeros = Enfermero.objects.all()
    print(f"Total de enfermeros en SQLite: {enfermeros.count()}")
    
    for enfermero in enfermeros:
        try:
            enfermero_mongo = EnfermeroMongo.objects(usuario_id=enfermero.usuario.id).first()
            if enfermero_mongo:
                print(f"✅ Enfermero {enfermero.usuario.username} existe en MongoDB")
            else:
                print(f"❌ Enfermero {enfermero.usuario.username} NO existe en MongoDB - sincronizando...")
                sync_nurse_to_mongo(enfermero)
        except Exception as e:
            print(f"❌ Error al verificar enfermero {enfermero.usuario.username}: {e}")
    
    print("=== Verificación completada ===")