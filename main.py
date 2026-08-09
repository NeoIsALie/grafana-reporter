import asyncio
import os
from datetime import date

from jinja2 import Environment, FileSystemLoader
import httpx
from dotenv import load_dotenv

from config import Config
from dashboard import Dashboard

load_dotenv()


async def list_dashboards(config: Config) -> list[str]:
   search_endpoint = f"{config.url}/api/search"
   async with httpx.AsyncClient() as client:
       response = await client.get(search_endpoint)
       dash_list = []
       if response.status_code == 200:
           dash_list = [
               dashboard.get('uid')
               for dashboard in response.json()
               if dashboard.get('type') == 'dash-db'
           ]

       return dash_list


async def main():
    config = Config()
    headers = {
        "Content-Type": "application/json"
    }
    headers["Authorization"] = f"Bearer {os.getenv('GRAFANA_TOKEN')}"
    request_date = date.today()
    client = httpx.AsyncClient()
    dashs = await list_dashboards(config)
    dashboard = Dashboard(uid=dashs[0], client=client)
    await dashboard.get_dashboard()
    dashboard.get_variables()
    dashboard.list_panels()

    for panel in dashboard.panels:
        await panel.render_image()

    main_panels = [panel for panel in dashboard.panels if panel.parent_panel is None]
    main_panels.sort(key=lambda p: p.panel_id)


    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("report.j2")

    html = template.render(panels=main_panels, config=config, request_date=request_date, dashboard=dashboard)
    with open("output_report_new.html", "w", encoding="utf-8") as f:
        f.write(html)

asyncio.run(main())
