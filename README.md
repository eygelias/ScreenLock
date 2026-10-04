# ScreenLock

ScreenLock es una aplicación de código abierto para Windows que te permite bloquear tu teclado y ratón de forma segura sin tener que apagar la pantalla ni suspender la PC. Es ideal para proteger tu equipo de toques accidentales o uso no autorizado cuando te alejas por un momento, manteniendo visible todo lo que está en pantalla.

## 🚀 Características
- **Bloqueo Rápido**: Define una combinación de teclas personalizada (ej. `Ctrl+Shift+F`) para bloquear y desbloquear tu PC al instante.
- **Contraseña Invisible**: Escribe tu contraseña secreta en tu teclado (a ciegas) para desbloquear la computadora.
- **Protección Total**: Mientras está bloqueada, el ratón y el teclado quedan completamente inhabilitados y congelados.
- **Invisible y Ligero**: Se ejecuta silenciosamente en segundo plano sin consumir apenas recursos de tu PC.
- **Autoinicio**: Puedes configurarlo para que inicie automáticamente junto con Windows.
- **Modo Oscuro/Claro**: La interfaz se adapta automáticamente a los colores de tu sistema operativo o te permite fijar el modo de tu preferencia de forma manual.
- **Portabilidad**: Es un único archivo ejecutable (`.exe`) que no requiere una instalación invasiva.

## 📥 Descarga y Uso
1. Ve a la sección de **[Releases](https://github.com/eygelias/ScreenLock/releases)** en este repositorio (a la derecha).
2. Descarga el archivo `ScreenLock.exe`.
3. Ejecútalo. Verás la ventana de configuración:
   - Define tu **Contraseña de Desbloqueo**.
   - Haz clic en el campo de **Teclas para Bloquear** y pulsa tu combinación deseada.
   - Haz clic en **Guardar Cambios**.
4. Haz clic en **Iniciar** para activar la protección de fondo.
5. ¡Listo! Usa tu combinación de teclas para congelar la PC. Para descongelarla, escribe tu contraseña en el teclado, o pulsa de nuevo tu combinación de teclas.

## 🛠️ Cómo funciona técnicamente
ScreenLock intercepta de forma segura los eventos de hardware a bajo nivel mediante la API de Windows (`SetWindowsHookExW` con `WH_KEYBOARD_LL` y `WH_MOUSE_LL`). Cuando se activa el bloqueo, el *hook* detiene la propagación de todos los clics del ratón y pulsaciones del teclado hacia el sistema operativo, permitiendo pasar únicamente las teclas que forman parte de la contraseña de desbloqueo o del atajo definido.

## 🛑 Opciones Avanzadas
Si en algún momento deseas apagar ScreenLock por completo y asegurarte de que no inicie más con tu PC, abre `ScreenLock.exe` y pulsa el botón rojo **"Detener y desactivar servicio de Windows"**. El programa se apagará completamente de raíz sin dejar rastro de ejecución.

## 📄 Licencia
Este proyecto es de código abierto y está disponible bajo los términos de la Licencia MIT. ¡Siéntete libre de colaborar o realizar un *fork*!


---
**SEO Tags:** $tags
