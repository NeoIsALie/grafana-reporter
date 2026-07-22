import os
from httpx import Timeout
from urllib.parse import urlencode
import httpx
from dotenv import load_dotenv
import base64

load_dotenv()


class PanelDoesNotExistError(Exception):
    def __init__(self, panel_id, dashboard):
        super().__init__(f"Panel with ID {panel_id} does not exist in dashboard '{dashboard.title}'")
        self.panel_id = panel_id
        self.dashboard = dashboard


class Panel:
    def __init__(
            self, 
            panel_id: int,
            dashboard_uid: str,
            title: str, 
            panel_type: str,
            position: dict,
            variables: dict,
        ) -> None:
        self._panel_id = panel_id
        self._title = title
        self.panel_type = panel_type
        self.x = position['x']
        self.y = position['y']
        self.width = position['w']
        self.height = position['h']
        self.embedded_image : bytes | None = None
        self.dashboard_uid = dashboard_uid
        self.variables: dict = variables
        self.render_url = ""

    @property
    def panel_id(self):
        return self._panel_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def position(self) -> dict:
        return {'x': self.x, 'y': self.y, 'w': self.width, 'h': self.height}

    def get_render_url(self):
        params: dict[str, str] = {
            'orgId': '1',
            'hideLogo': 'true',
            'width': '1000',
            'height': '500',
            'viewPanel': f'panel-{self._panel_id}',
            'panelId' : f'panel-{self._panel_id}'
        }
        params.update(self.variables)
        encoded_params = urlencode(params)
        self.render_url = f"{os.getenv('GRAFANA_URL')}/render/d-solo/{self.dashboard_uid}?{encoded_params}"

    async def render_image(self) -> None:
        self.get_render_url()
        timeout = Timeout(connect=120.0, read=120.0, write=3.0, pool=2.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(self.render_url)
            if response.status_code == httpx.codes.OK:
                self.embedded_image = base64.b64encode(response.content).decode("ascii")