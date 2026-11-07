

import argparse
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

API_URL = "https://nvapi.nicovideo.jp/v2/users/{}/videos"

HEADERS = {
    "X-Frontend-ID": "6",
    "X-Frontend-Version": "0",
    "X-Niconico-Language": "ja-jp",
    "User-Agent": "Mozilla/5.0",
}


def fetch_page(user_id, page, page_size=100):
    params = {
    "sortKey": "registeredAt",
    "sortOrder": "desc",
    "pageSize": page_size,
    "page": page,
}

    url = API_URL.format(user_id) + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(url, headers=HEADERS)

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", default="videos.txt")
    args = parser.parse_args()

    if not args.user_id.isdigit():
        raise ValueError("Invalid user ID")

    video_urls = []
    seen = set()

    page_size = 100
    max_pages = 100

    for page in range(1, max_pages + 1):
        print(f"Fetching page {page}...")

        data = fetch_page(args.user_id, page, page_size)

        if data.get("meta", {}).get("status") != 200:
            raise RuntimeError(f"API error: {data.get('meta')}")

        result = data.get("data") or {}
        items = result.get("items") or []
        total_count = result.get("totalCount", 0)

        print(f"API totalCount: {total_count}")
        print(f"Items returned: {len(items)}")

        # 空のページなら必ず終了
        if not items:
            print("Empty page detected. Stopping.")
            break

        added = 0

        for item in items:
            essential = item.get("essential") or {}
            video_id = essential.get("id")

            if not video_id:
                continue

            url = f"https://www.nicovideo.jp/watch/{video_id}"

            if url not in seen:
                seen.add(url)
                video_urls.append(url)
                added += 1

        print(f"Added: {added}")
        print(f"Total collected: {len(video_urls)}")

        # APIの総件数に到達
        if len(video_urls) >= total_count:
            break

        # 最終ページ
        if len(items) < page_size:
            break

        time.sleep(1)

    if not video_urls:
        raise RuntimeError("No videos found. Output was not created.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        "\n".join(video_urls) + "\n",
        encoding="utf-8"
    )

    print("=" * 40)
    print(f"SUCCESS: {len(video_urls)} videos collected")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
