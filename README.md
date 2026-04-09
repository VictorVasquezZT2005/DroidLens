# DroidLens

DroidLens es una herramienta gráfica (GUI) potente y sencilla diseñada **exclusivamente para macOS (Catalina en adelante)** que facilita la grabación de pantalla y el control de dispositivos Android. Utiliza la potencia de `scrcpy` y `adb` para ofrecer una experiencia fluida y profesional.


## Características

- **Compatibilidad:** Diseñado específicamente para macOS Catalina y versiones superiores.
- **Detección Automática:** Encuentra y conecta tus dispositivos Android vía ADB al instante.
- **Información del Dispositivo:** Visualiza la resolución nativa y la orientación del dispositivo.
- **Calidad Personalizable:** Elige entre múltiples resoluciones (Original, FHD, HD, etc.) para tus grabaciones.
- **Grabación Flexible:**
  - Grabación con o sin vista previa en vivo.
  - Soporte para audio interno (Android 10+) o micrófono del dispositivo.
- **Interfaz Moderna:** Estética inspirada en macOS con soporte nativo para Modo Oscuro/Claro.

## Requisitos Previos

Para que DroidLens funcione correctamente, **debes tener instalados** en tu Mac los siguientes componentes:

1.  **Platform Tools (ADB):** Tener instalado PlatformTools en /Users/---/Library/Android/sdk/platform-tools
2.  **scrcpy:** dentro de la carpeta de PlatformTools

## Instalación y Uso

1. Ve a la sección de **[Releases](https://github.com/VictorVasquezZT2005/DroidLens/releases)** de este repositorio.
2. Descarga la última versión de la aplicación (`.app` o instalador).
3. Abre la aplicación y comienza a grabar.

## Notas de Configuración

- Asegúrate de tener habilitada la **Depuración USB** en tu dispositivo Android.
- El audio interno requiere que el dispositivo ejecute **Android 10 o superior**.
- La aplicación busca las herramientas en sus rutas estándar de macOS. Asegúrate de que `scrcpy` y `adb` sean accesibles desde la terminal.

## Licencia

Este proyecto es de **código visible (Source-Available)** pero no es modificable. Puedes ver, descargar y ejecutar el software para uso personal y educativo, pero **no está permitida la modificación, redistribución de versiones modificadas o uso comercial** sin permiso explícito del autor original.

Mira el archivo [LICENSE](LICENSE) para conocer los términos completos.

---
Desarrollado por [Victor Vasquez](https://github.com/VictorVasquezZT2005)
