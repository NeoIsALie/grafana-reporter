import asyncio
from urllib.parse import urlencode
import httpx
import base64

from config import get_config

conf = get_config()


class PanelRenderError(Exception):
    pass


class Panel:
    def __init__(
        self,
        panel_id: int,
        dashboard_uid: str,
        title: str,
        panel_type: str,
        variables: dict,
        parent_panel: int | None = None,
    ) -> None:
        self.panel_id = panel_id
        self.title = title
        self.panel_type = panel_type
        self.parent_panel = parent_panel
        self.embedded_image: str | None = None
        self.dashboard_uid = dashboard_uid
        self.variables: dict = variables
        self.render_url = ""
        self.children_panels: list[int] | None = None

    @property
    def get_render_url(self):
        params: dict[str, str] = {
            "orgId": "1",
            "hideLogo": "true",
            "width": "1000",
            "height": "500",
            "viewPanel": f"panel-{self.panel_id}",
            "panelId": f"panel-{self.panel_id}",
        }
        params.update(self.variables)
        encoded_params = urlencode(params)
        return f"{conf.url}/render/d-solo/{self.dashboard_uid}?{encoded_params}"

    async def render_image(
        self, client: httpx.AsyncClient, semaphore: asyncio.Semaphore
    ) -> None:
        async with semaphore:
            response = await client.get(self.get_render_url)
        self.embedded_image = base64.b64encode(response.content).decode("ascii")
