import asyncio
import os
import time
from jinja2 import Environment, FileSystemLoader
import httpx
from dotenv import load_dotenv
from dashboard import Dashboard

load_dotenv()


USE_API_KEY = True


headers = {
   "Content-Type": "application/json"
}


if USE_API_KEY:
   headers["Authorization"] = f"Bearer {os.getenv('GRAFANA_TOKEN')}"



async def list_dashboards() -> list:
   search_endpoint = f"{os.getenv("GRAFANA_URL")}/api/search"
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
    client = httpx.AsyncClient()
    dashs = await list_dashboards()
    dashboard = Dashboard(uid=dashs[0], client=client)
    await dashboard.get_dashboard()
    dashboard.get_variables()
    dashboard.list_panels()
    for panel in dashboard.panels:
        await panel.render_image()
        time.sleep(3)

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("report.html")

    html = template.render(panels=dashboard.panels)
    with open("output_report.html", "w", encoding="utf-8") as f:
        f.write(html)
asyncio.run(main())

