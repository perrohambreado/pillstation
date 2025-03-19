# Crear enfermero
User = get_user_model()

def crear_enfermero(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        enfermero_form = EnfermeroForm(request.POST)

        if user_form.is_valid() and enfermero_form.is_valid():
            username = user_form.cleaned_data['username']

            if User.objects.filter(username=username).exists():
                usuario_existente = User.objects.get(username=username)
                if hasattr(usuario_existente, 'enfermero'):
                    enfermero_form.add_error('usuario', 'Este usuario ya tiene un enfermero asignado.')
                    messages.error(request, 'Error: Este usuario ya tiene un enfermero.')
                    return render(request, 'nurse/create.html', {'user_form': user_form, 'enfermero_form': enfermero_form})

                usuario_existente.is_staff = True
                usuario_existente.save()

                nuevo_enfermero = enfermero_form.save(commit=False)
                nuevo_enfermero.usuario = usuario_existente
                nuevo_enfermero.save()
                messages.success(request, 'Enfermero creado Existosamente') 
                return redirect('listar_enfermeros')     
            
            nuevo_usuario = user_form.save(commit=False)
            nuevo_usuario.tipo_usuario = 'enfermero'  # Forzar a que sea enfermero
            nuevo_usuario.is_staff = True
            nuevo_usuario.is_superuser = False  # Generalmente un enfermero no es superusuario
            nuevo_usuario.save()

            nuevo_usuario._skip_signal = True
            nuevo_usuario.save()

            nuevo_enfermero = enfermero_form.save(commit=False)   
            nuevo_enfermero.usuario = nuevo_usuario
            nuevo_enfermero.save()  


            sync_nurse_to_mongo(nuevo_enfermero)

            messages.success(request, 'Enfermero creado exitosamente.')
            return redirect('listar_enfermeros')
        else:
            print("Errores en user_form:", user_form.errors)
            print("Errores en enfermero_form:", enfermero_form.errors)
            messages.error(request, 'Error al crear el administrador.')
    else:
        user_form = CustomUserCreationForm()
        enfermero_form = EnfermeroForm()
    
    return render(request, 'nurse/create.html', {'user_form': user_form, 'enfermero_form': enfermero_form})
