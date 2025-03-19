class AuthRouter:
    route_app_labels = {"auth", "contenttypes", "admin", "sessions"}
    
    sqlite_models = {"user", "administrador", "enfermero", "enfermeropastillero"}
    
    mongo_models = {"mongoadministrador", "mongoenfermero"}
    
    def db_for_read(self, model, **hints):
        model_name = model._meta.model_name.lower()
        
        if model._meta.app_label in self.route_app_labels:
            return "default"
            
        if model_name in self.sqlite_models:
            return "default"
            
        if model_name in self.mongo_models:
            return "mongodb"
            
        return None

    def db_for_write(self, model, **hints):
        model_name = model._meta.model_name.lower()
        
        if model._meta.app_label in self.route_app_labels:
            return "default"
            
        if model_name in self.sqlite_models:
            return "default"
            
        if model_name in self.mongo_models:
            return "mongodb"
            
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Permite relaciones entre modelos que están en la misma base de datos"""
        obj1_model = obj1._meta.model_name.lower()
        obj2_model = obj2._meta.model_name.lower()
        
        # Permitir relaciones entre modelos de SQLite
        if (obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels or
            obj1_model in self.sqlite_models or
            obj2_model in self.sqlite_models):
            return True
            
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla qué migraciones van a qué base de datos"""
        if model_name is None:
            return None
            
        model_name = model_name.lower()
        
        # Apps core siempre a SQLite
        if app_label in self.route_app_labels:
            return db == "default"
            
        # Modelos principales a SQLite
        if model_name in self.sqlite_models:
            return db == "default"
            
        # Modelos espejo a MongoDB
        if model_name in self.mongo_models:
            return db == "mongodb"
            
        return None