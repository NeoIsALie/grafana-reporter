import os
from typing import List

from httpx import AsyncClient
from panel import Panel
from dotenv import load_dotenv

load_dotenv()

class Dashboard:
    def __init__(self, client: AsyncClient, uid: str):
        self.client = client
        self.uid = uid
        self._title = None
        self.dashboard_json = None
        self.variables = None
        self.panels: List[Panel] | None = None


    @property
    def title(self):
        return self._title

    @property
    def date_range(self):
        return f"{self.variables['from']} to {self.variables['to']}"


    def print_variables(self):
        return ", ".join(f"{k}={v}" for k, v in self.variables.items())

    async def get_dashboard(self) -> None:
        search_endpoint = f"{os.getenv("GRAFANA_URL")}/api/dashboards/uid/{self.uid}"
        response = await self.client.get(search_endpoint)
        self.dashboard_json = response.json()
        self._title = self.dashboard_json["dashboard"]["title"]

    def get_variables(self) -> None:
        self.variables = dict()
        templates = self.dashboard_json['dashboard']['templating']["list"]
        for item in templates:
            self.variables[f"var-{item["name"]}"] = item['current']['value']
        self.variables["from"] = self.dashboard_json["dashboard"]['time']['from']
        self.variables["to"] = self.dashboard_json["dashboard"]['time']['to']

    def list_panels(self):
        panels = self.dashboard_json['dashboard'].get("panels", [])
        self.panels = []
        if panels is not None:
            for panel in panels:
                if not panel.get('panels'):
                    self.panels.append(
                        Panel(
                            panel_id=panel.get('id'),
                            title=panel.get('title'),
                            panel_type=panel.get('type'),
                            position=panel["gridPos"],
                            dashboard_uid=self.uid,
                            variables=self.variables,
                        )
                    )
                else:
                    panel_cls = Panel(
                            panel_id=panel.get('id'),
                            title=panel.get('title'),
                            panel_type=panel.get('type'),
                            position=panel["gridPos"],
                            dashboard_uid=self.uid,
                            variables=self.variables,
                        )
                    panel_cls.children_panels = []
                    for extra_panel in panel['panels']:
                        self.panels.append(
                            Panel(
                                panel_id=extra_panel.get('id'),
                                title=extra_panel.get('title'),
                                panel_type=extra_panel.get('type'),
                                position=extra_panel["gridPos"],
                                dashboard_uid=self.uid,
                                variables=self.variables,
                                parent_panel=extra_panel.get('id')
                            )
                        )
                        panel_cls.children_panels.append(extra_panel.get('id'))
                    self.panels.append(panel_cls)

    def get_panel(self, panel_id: int) -> Panel:
        for panel in self.panels:
            if panel.panel_id == panel_id:
                return panel
