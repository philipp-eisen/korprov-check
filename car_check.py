import asyncio
import datetime
from pathlib import Path
from time import sleep

import requests
from pyppeteer import launch

SCREENSHOT_DIR = Path("screenshots")
CITIES = [
    "Enköping",
    "Farsta",
    "Järfälla",
    "Norrtälje 2",
    "Nynäshamn",
    "Södertälje",
    "Tullinge",
    "Uppsala",
    "Västerås",
    "Sollentuna",
]


async def check_appointment(city: str):
    browser = await launch(options={"headless": True, "args": ["--no-sandbox"]})
    page = await browser.newPage()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M-%S")
    await page.setViewport({"width": 1920, "height": 1080})
    await page.goto("https://fp.trafikverket.se/boka/#/search/WOIHSworMpwMMa/5/0/0/0")
    await page.waitForSelector("#examination-type-select")
    await page.select("#examination-type-select", "12")
    await page.select("#vehicle-select", "4")
    await asyncio.sleep(1)
    await page.waitForSelector("#id-control-searchText-1-1")
    await page.focus("#id-control-searchText-1-1")
    await page.keyboard.type(city)
    await page.keyboard.press("Enter")
    await asyncio.sleep(3)
    await page.click("#id-control-searchText-1-1")
    await page.keyboard.press("Enter")
    await asyncio.sleep(10)

    no_appointments = await page.evaluate(
        "document.querySelector('body > div.container-fluid').innerText.includes('Hittade inga')"
    )
    if no_appointments:
        send_on_slack(f"No appointments in {city}")

    else:
        screenshot_path = SCREENSHOT_DIR / f"{now}.png"
        await page.screenshot({"path": str(screenshot_path)})
        send_on_slack(f"<@U01RYQ50ZFU> <U01RYAQ7XBM> Probably appointments in {city}")
    await browser.close()
    return not no_appointments


def send_on_slack(text):

    slack_token = "TOKEN-HERE"
    slack_channel = "#körprov"
    slack_icon_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTuGqps7ZafuzUsViFGIremEL2a3NR0KO0s0RTCMXmzmREJd5m4MA&s"
    slack_user_name = "Checki the Checker"

    return requests.post(
        "https://slack.com/api/chat.postMessage",
        {
            "token": slack_token,
            "channel": slack_channel,
            "text": text,
            "link_names": 1,
            "icon_url": slack_icon_url,
            "username": slack_user_name,
            "blocks": None,
            "as_user": True,
        },
    ).json()


if __name__ == "__main__":
    SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)
    check_every_s = 60 * 60
    i = 0
    while True:
        if i % 24 == 0:
            print(send_on_slack("Script is still checking"))
        try:
            for city in CITIES:
                asyncio.get_event_loop().run_until_complete(check_appointment(city))
            sleep(check_every_s)
        except Exception as e:
            print(e)
            if isinstance(e, KeyboardInterrupt):
                raise KeyboardInterrupt
        i += 1
