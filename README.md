
<img width="1207" height="512" alt="logo@2" src="https://github.com/user-attachments/assets/fb4aab0b-a239-4b89-b305-fcb233fd2f13" />

# Open Harbor Server — Integración para Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/PuertoDeMogan/openharbor_sender)](https://github.com/PuertoDeMogan/OpenHarbor_sender/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Actualiza los datos de tu puerto marítimo directamente en Home Assistant. Open Harbor Sender se conecta al repositorio [OpenHarbor Data](https://github.com/PuertoDeMogan/OpenHarbor_Data) y modifica los sensores automáticamente según los datos de los sensores seleccionados.

---

## Características

- 🌊 Actualizacion de los sensores del puerto marítimo
- 🔄 Intervalo de actualización configurable (en minutos)

---

## Requisitos

- Home Assistant **2024.1.0** o superior
- [HACS](https://hacs.xyz) instalado

---

## Instalación

### Mediante HACS (recomendado)

1. Abre HACS en tu instancia de Home Assistant
2. Ve a **Integraciones** → menú de tres puntos → **Repositorios personalizados**
3. Añade `https://github.com/PuertoDeMogan/openharbor_sender` como **Integración**
4. Busca **Open Harbor** y haz clic en **Descargar**
5. Reinicia Home Assistant

### Manual

<details>
  
<summary>Fuera de HACS</summary>  

1. Descarga la última versión desde [GitHub Releases](https://github.com/PuertoDeMogan/openharbor_sender/releases)
2. Copia la carpeta `custom_components/openharbor_sender/` en el directorio `config/custom_components/` de tu instalación de HA
3. Reinicia Home Assistant

</details>

---

## Configuración

Para añadir la integración a tu instancia de Home Assistant, usa el botón:
<p>
    <a href="https://my.home-assistant.io/redirect/config_flow_start?domain=openharbor_sender" class="my badge" target="_blank">
        <img src="https://my.home-assistant.io/badges/config_flow_start.svg">
    </a>
</p>

### Configuración Manual
1. Ve a **Configuración → Integraciones → Añadir integración**
2. Busca **Open Harbor Sender**

<img width="563" height="293" alt="image" src="https://github.com/user-attachments/assets/3253fc6e-b8a4-4f2a-a5f4-bbd61da85d5b" />

3. Añade el token de edicion de Github que te lo proporcionara el administrador de @PuertoDeMogan y el puerto a modificar:

<img width="561" height="307" alt="image" src="https://github.com/user-attachments/assets/8b9056eb-be0b-454e-ad5d-9289706b4275" />


4. Selecciona los sensores que quieres vincular a los datos en los desplegables.
<img width="570" height="960" alt="image" src="https://github.com/user-attachments/assets/f838b235-2035-408d-b314-88f8f74a6996" />


5. Establece el intervalo de actualización (por defecto: 5 minutos)
<img width="567" height="221" alt="image" src="https://github.com/user-attachments/assets/dff411f3-169a-41ed-b689-3bc92364b1eb" />


6. Haz clic en **Enviar**

---

## Sensores

Los sensores vinculados se actualizaran **dinámicamente** según el intervalo y los datos de los sensores seleccionadosdisponibles de cada puerto. El número y tipo de sensores puede variar entre puertos.
<img width="1048" height="840" alt="image" src="https://github.com/user-attachments/assets/2b890f13-e292-49f9-bd4b-b0a67331c86b" />


---

## Puertos disponibles

El puerto actualizar los sensores disponibles del [repositorio OpenHarbor Data](https://github.com/PuertoDeMogan/OpenHarbor_Data/tree/main/ports). A medida que se añadan nuevos sensores al fichero del puerto, estarán disponibles para la actualizacion de ellos en el asistente de configuración de la integración.

Actualmente disponibles:

| Puerto | ID |
|---|---|
| Puerto de Mogán | `puerto_mogan` |

---

## Opciones

Tras la configuración inicial, puedes modificarla en cualquier momento:

1. Ve a **Configuración → Integraciones**
2. Localiza **Open Harbor** y haz clic en **Configurar**
3. Actualiza los puertos seleccionados o el intervalo de actualización
4. Haz clic en **Enviar** — la integración se recargará automáticamente

---

## Solución de problemas

**Los sensores no actualizan**
- Comprueba que tu instancia de Home Assistant tiene acceso a internet
- Verifica que la integración se cargó correctamente en **Configuración → Sistema → Registros**

**Error `Token inválido o sin permisos` durante la configuración**
- El token no es valio o ha caducado, pide al administrador del repositorio que cree otro para poder modificar los datos.

**Un sensor desapareció de la integracion**
- Se ha modificado el fichero de datos del puerto y ya no aparece en HA, modifique manualmente el fichero y vuelva a crearlo con la estructura correcta.

---


## Contribuir

¡Las contribuciones son bienvenidas! Abre un issue o pull request en [GitHub](https://github.com/PuertoDeMogan/openharbor_sender).

Para añadir un nuevo puerto, hay que configurar el [repositorio OpenHarbor Data](https://github.com/PuertoDeMogan/OpenHarbor_Data) y crear al puerto un nuevo Token Valido de edicion del repositorio.

---

## Licencia

Licencia MIT — consulta el archivo [LICENSE](LICENSE) para más detalles.


