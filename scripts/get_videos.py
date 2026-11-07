
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_URL = "https://nvapi.nicovideo.jp/v3/users/{}/videos"

HEADERS = {
    "X-Frontend-Id": "6",
    "X-Frontend-Version": "0",
    "User-Agent": "NiconicoVideoListCollector/1.0",
}


def fetch_page(user_id, page, page_size):
    params = {
        "sortKey": "registeredAt",
        "sortOrder": "desc",
        "sensitiveContents": "mask",
        "pageSize": page_size,
        "page": page,
    }

    url = API_URL.format(user_id) + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers=HEADERS)

    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == 3:
                raise
            print(f"Retry {attempt + 1}: {error}")
            time.sleep(2 ** attempt)


def extract_video_id(item):
    video = item.get("video", item)

    if not isinstance(video, dict):
        return None

    return (
        video.get("id")
        or video.get("watchId")
        or video.get("contentId")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--output", default="videos.txt")
    args = parser.parse_args()

    if not args.user_id.isdigit():
        raise ValueError("User ID must contain digits only.")

    video_ids = []
    seen = set()

    for page in range(1, args.max_pages + 1):
        print(f"Fetching page {page}...")

        result = fetch_page(
            args.user_id,
            page,
            args.page_size
        )

        if result.get("meta", {}).get("status", 200) != 200:
            raise RuntimeError(f"API error: {result.get('meta')}")

        data = result.get("data") or {}
        items = data.get("items") or []

        if not items:
            print("No more videos.")
            break

        added = 0

        for item in items:
            video_id = extract_video_id(item)

            if not video_id or video_id in seen:
                continue

            seen.add(video_id)
            video_ids.append(
                f"https://www.nicovideo.jp/watch/{video_id}"
            )
            added += 1

        print(f"Added: {added} / Total: {len(video_ids)}")

        if len(items) < args.page_size:
            break

        time.sleep(1)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(video_ids) + ("\n" if video_ids else ""),
        encoding="utf-8"
    )

    print(f"Completed: {len(video_ids)} videos")
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()
