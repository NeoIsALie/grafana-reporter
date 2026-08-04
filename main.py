import asyncio
import base64
import os
import time
from copy import copy
from datetime import date

import requests
from httpx import Timeout
from jinja2 import Environment, FileSystemLoader
import httpx
from dotenv import load_dotenv

from config import Config
from dashboard import Dashboard

load_dotenv()


USE_API_KEY = True


headers = {
   "Content-Type": "application/json"
}


if USE_API_KEY:
   headers["Authorization"] = f"Bearer {os.getenv('GRAFANA_TOKEN')}"



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


async def render(client: httpx.AsyncClient, url: str, semaphore: asyncio.BoundedSemaphore) -> str:
    response = await client.get(url)
    if response.status_code == httpx.codes.OK:
        return base64.b64encode(response.content).decode("ascii")


async def main():
    config = Config()
    request_date = date.today()
    client = httpx.AsyncClient()
    dashs = await list_dashboards(config)
    dashboard = Dashboard(uid=dashs[0], client=client)
    await dashboard.get_dashboard()
    dashboard.get_variables()
    dashboard.list_panels()
    panels = copy(dashboard.panels)
    start = time.time()
    for panel in dashboard.panels:
        await panel.render_image()

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("report.j2")

    html = template.render(panels=panels, config=config, request_date=request_date, dashboard=dashboard)
    with open("output_report_new.html", "w", encoding="utf-8") as f:
        f.write(html)
    stop = time.time()
    print(f"report generated in {stop - start:.2f} seconds")
asyncio.run(main())

