# Cómo Capturar Audio del Sistema en Windows

## Opción 1: Habilitar "Stereo Mix" (Mezcla estéreo)

**Stereo Mix** es un dispositivo virtual de Windows que captura todo el audio que se reproduce en tu computadora.

### Pasos para habilitar:

1. **Haz clic derecho** en el ícono del altavoz en la barra de tareas
2. Selecciona **"Configuración de sonido"** o **"Sonidos"**
3. Ve a la pestaña **"Grabación"** (Recording)
4. **Haz clic derecho en un espacio vacío** y marca:
   - ✅ **"Mostrar dispositivos deshabilitados"** (Show Disabled Devices)
   - ✅ **"Mostrar dispositivos desconectados"** (Show Disconnected Devices)
5. Busca **"Mezcla estéreo"** o **"Stereo Mix"**
6. **Haz clic derecho** sobre él y selecciona **"Habilitar"**
7. **Opcional**: Haz clic derecho → **"Establecer como dispositivo predeterminado"**

### Después de habilitar:

- **Reinicia EchoPy**
- La aplicación detectará automáticamente Stereo Mix
- Verás en consola: `"Using loopback device for system audio capture"`

---

## Opción 2: Si Stereo Mix no aparece

Algunos sistemas no tienen Stereo Mix. Alternativas:

### A) Actualizar driver de audio:

1. Abre **Administrador de dispositivos**
2. Expande **"Controladores de sonido..."**
3. Clic derecho en tu dispositivo de audio → **Actualizar driver**
4. Reinicia y verifica si Stereo Mix aparece

### B) Usar VB-Audio Virtual Cable (gratuito):

1. Descarga desde: https://vb-audio.com/Cable/
2. Instala VB-CABLE Driver
3. En configuración de sonido:
   - **Reproducción**: Establece "CABLE Input" como predeterminado
   - **Grabación**: Usa "CABLE Output"
4. En EchoPy Settings: Selecciona "CABLE Output"

---

## Verificar que funciona:

1. **Reproduce música** en cualquier aplicación
2. En EchoPy deberías ver:
   - `Audio: 0.050` o valores más altos (en lugar de 0.0001)
   - Las barras/visualización se mueven con la música

---

## Solución de Problemas:

### "Audio: 0.0001" (muy bajo)

- ✅ Stereo Mix no está habilitado o no está siendo usado
- ✅ El volumen del sistema está muy bajo
- ✅ No hay música/audio reproduciéndose

### "No loopback device found"

- ✅ Sigue los pasos de la Opción 1 arriba
- ✅ O instala VB-Audio Virtual Cable (Opción 2B)

### Stereo Mix funciona pero bajo volumen

1. Clic derecho en Stereo Mix → **Propiedades**
2. Pestaña **"Niveles"**
3. Sube el nivel de Stereo Mix a 100%

---

**Nota**: Después de habilitar Stereo Mix **NO necesitas** cambiar nada en EchoPy - se detecta automáticamente al iniciar.
