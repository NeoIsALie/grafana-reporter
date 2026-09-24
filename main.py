import asyncio
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader
import httpx

from config import Config
from dashboard import Dashboard


async def list_dashboards(config: Config) -> list[str]:
    search_endpoint = f"{config.url}/api/search"
    async with httpx.AsyncClient() as client:
        response = await client.get(search_endpoint)
        dash_list = []
        if response.status_code == 200:
            dash_list = [
                dashboard.get("uid")
                for dashboard in response.json()
                if dashboard.get("type") == "dash-db"
            ]

        return dash_list


async def main():
    config = Config()
    request_date = datetime.now(timezone.utc).astimezone()
    client = httpx.AsyncClient()
    dashs = await list_dashboards(config)
    dashboard = Dashboard(uid=dashs[0], client=client)
    await dashboard.get_dashboard()
    dashboard.get_variables()
    dashboard.list_panels()

    timeout = httpx.Timeout(
        connect=15.0,
        read=60.0,
        write=10.0,
        pool=15.0,
    )

    limits = httpx.Limits(
        max_connections=20,
        max_keepalive_connections=20,
    )

    semaphore = asyncio.Semaphore(5)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        await asyncio.gather(
            *(panel.render_image(client, semaphore) for panel in dashboard.panels)
        )

    main_panels = [panel for panel in dashboard.panels if panel.parent_panel is None]
    main_panels.sort(key=lambda p: p.panel_id)

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("report.j2")

    html = template.render(
        panels=main_panels,
        config=config,
        request_date=request_date,
        dashboard=dashboard,
    )
    with open("output_report_new.html", "w", encoding="utf-8") as f:
        f.write(html)


asyncio.run(main())
