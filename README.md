# OpenHarbor Sender

Integración de Home Assistant para publicar los sensores de tu puerto en [Open Harbor Data](https://github.com/PuertoDeMogan/OpenHarbor_Data).

## Instalación

1. Copia `custom_components/OpenHarbor_Sender/` en tu directorio `config/custom_components/`
2. Reinicia Home Assistant
3. Ve a **Configuración → Integraciones → Añadir integración → Open Sender Sender**

## Requisitos

- Un [Fine-grained token de GitHub](https://github.com/settings/tokens?type=beta) con permisos de lectura y escritura sobre `PuertoDeMogan/OpenHarbor_Data`
- El fichero `ports/{port_id}.json` debe existir previamente en el repositorio de datos
