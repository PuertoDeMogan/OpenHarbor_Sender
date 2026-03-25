DOMAIN = "openharbor_sender"

DATA_REPO_OWNER = "PuertoDeMogan"
DATA_REPO_NAME = "openharbor_data"
DATA_REPO_BRANCH = "main"

DATA_API_BASE = (f"https://api.github.com/repos/{DATA_REPO_OWNER}/{DATA_REPO_NAME}/contents/ports")
DATA_RAW_BASE = (f"https://raw.githubusercontent.com/{DATA_REPO_OWNER}/{DATA_REPO_NAME}/main/ports")

CONF_PORT_ID = "port_id"
CONF_GITHUB_TOKEN = "github_token"
CONF_SENSOR_MAP = "sensor_map"
CONF_UPDATE_INTERVAL = "update_interval"

UPDATE_INTERVAL_OPTIONS = [5, 10, 15, 30, 60, 120]
DEFAULT_UPDATE_INTERVAL = 10

AVAILABLE_PORTS = {
    "puerto_mogan": "Puerto de Mogán",
}
