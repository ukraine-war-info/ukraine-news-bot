import asyncio
import aiohttp
from console import Console
from datetime import datetime
from typing import Union

console = Console(True)

url = "https://push.api.bbci.co.uk/batch?t=%2Fdata%2Fbbc-morph-lx-commentary-data-paged%2FassetUri%2F%252Fnews%252Flive%252Fworld-europe-60532634%2FisUk%2Ffalse%2Flimit%2F20%2FnitroKey%2Flx-nitro%2FpageNumber%2F1%2FserviceName%2Fnews%2Fversion%2F1.5.6?timeout=5"

try:
    with open("latest", "r") as f:
        latest_id = f.read()

except FileNotFoundError:
    latest_id = ""

async def get_data() -> Union[dict, None]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            global latest_id

            latest = data["payload"][0]["body"]["results"][0]

            # This is just in case they post a new update while im still working on adding a new datatype
            # for i in data["payload"][0]["body"]["results"]:
            #     if i["assetId"] == "621a7884980bea49f4b7a320":
            #         latest = i

            if latest["assetId"] == latest_id:
                return None

            latest_id = latest["assetId"]

            title = latest["title"]
            content = "" # Gotten later
            image_url = None
            is_breaking = latest["options"]["isBreakingNews"]
            post_locator = latest["locator"]
            updated = datetime.strptime(latest["lastUpdated"].rstrip(":"), "%Y-%m-%dT%H:%M:%S%z")

            # Image
            try:
                for image_key in latest["media"]["images"]["body"]:
                    image_url = latest["media"]["images"]["body"][image_key]["href"]
                    break
            except: image_url = None

            # Content
            # TODO: Remake this to be more readable and less code re-write
            # It seems that every data type supports every other data type
            # -------
            # Right now it loops through every known data type and adds what is needed.
            for item in latest["body"]:

                try:
                    if item["name"] == "paragraph":
                        if len(item["children"]) == 1:
                            if item["children"][0]["name"] == "text":
                                content += item["children"][0]["text"].replace("\n", " ")

                            elif item["children"][0]["name"] == "link":
                                    text = child["children"][0]["children"][0]["text"]
                                    text_url = child["children"][2]["attributes"][1]["value"]

                                    content += f"[{text}]({text_url})"

                            elif item["children"][0]["name"] == "bold":
                                    content += "**" + item["children"][0]["children"][0]["text"].strip() + "**"

                        else:
                            for child in item["children"]:
                                if child["name"] == "text":
                                    content += child["text"].replace("\n\n", " ")

                                elif child["name"] == "link":
                                    text = child["children"][0]["children"][0]["text"]
                                    text_url = child["children"][2]["attributes"][1]["value"]

                                    content += f"[{text}]({text_url}) "

                                elif child["name"] == "bold":
                                        content += "**" + child["children"][0]["text"].strip() + "** "
                            
                        content += "\n\n"

                    elif item["name"] == "list":
                        for child in item["children"]:
                            if len(child["children"]) == 1:
                                if child["name"] == "listItem":
                                    content += " · " + child["children"][0]["text"].strip()
                            
                            else:
                                content += " · "
                                for sub_child in child["children"]:

                                    if sub_child["name"] == "text":
                                        content += sub_child["text"].strip() + " "

                                    elif sub_child["name"] == "link":
                                        text = sub_child["children"][0]["children"][0]["text"]
                                        text_url = sub_child["children"][2]["attributes"][1]["value"]

                                        content += f"[{text}]({text_url}) "

                                    elif sub_child["name"] == "bold":
                                        content += "**" + sub_child["children"][0]["text"].strip() + "** "

                            content += "\n\n"

                    elif item["name"] == "link":
                        text = item["children"][0]["children"][0]["text"]
                        text_url = item["children"][2]["attributes"][1]["value"]

                        content += f"[{text}]({text_url})\n\n"

                    elif item["name"] == "video":
                        content += "*There is a video, but the bot cannot display it. Please click on the link above to view it.*\n\n"

                    elif item["name"] == "quote":
                        if item["children"][0]["name"] == "quoteText":
                            content += "\"" + item["children"][0]["children"][0]["text"].replace("\"", "") + "\"\n\n"

                    elif item["name"] == "embed":
                        try:
                            if item["children"][0]["children"][0]["text"] == "twitter":
                                t_url = item["children"][1]["children"][0]["text"]
                                content += f"[Twitter]({t_url})\n\n"
                        except: pass

                except:
                    pass

                if len(content) > 4096:
                    content = content[:4093] + "..."
                    console.warn("Content is over 4096 chars long. Truncated.")
                    break

            content = content.strip()

            with open("latest", "w+") as f:
                f.write(latest_id)

            return {
                "title": title,
                "content": content,
                "is_breaking": is_breaking,
                "image": image_url,
                "locator": post_locator,
                "updated": updated
            }