
import argparse
from pathlib import Path
from yt_dlp import YoutubeDL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", default="videos.txt")
    args = parser.parse_args()

    if not args.user_id.isdigit():
        raise ValueError("Invalid user ID")

    url = f"https://www.nicovideo.jp/user/{args.user_id}/video"

    options = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": False,
        "ignoreerrors": False,
    }

    print(f"Target: {url}")

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise RuntimeError("Failed to retrieve user information")

    entries = info.get("entries")

    if entries is None:
        raise RuntimeError("No playlist entries returned")

    video_urls = []
    seen = set()

    for entry in entries:
        if not entry:
            continue

        video_id = entry.get("id")

        if not video_id:
            continue

        video_url = f"https://www.nicovideo.jp/watch/{video_id}"

        if video_url not in seen:
            seen.add(video_url)
            video_urls.append(video_url)

    if not video_urls:
        raise RuntimeError(
            "No videos found. Check the user ID and yt-dlp logs."
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        "\n".join(video_urls) + "\n",
        encoding="utf-8"
    )

    print(f"Successfully collected {len(video_urls)} videos")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
