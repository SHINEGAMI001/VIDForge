import yt_dlp


def get_video_info(url):
    options = {
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def get_qualities(info):
    qualities = set()

    for fmt in info.get("formats", []):
        height = fmt.get("height")

        if height:
            qualities.add(height)

    return sorted(qualities)


def download_video(url, quality):
    options = {
        "format": (
            f"bestvideo[height<={quality}]"
            f"+bestaudio/best[height<={quality}]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": "downloads/%(title)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])


def main():
    url = input("Enter YouTube URL: ").strip()

    if not url:
        print("No URL provided.")
        return

    print("\nFetching video information...")

    try:
        info = get_video_info(url)
    except Exception as e:
        print(f"\nCould not fetch video information:")
        print(e)
        return

    title = info.get("title", "Unknown")
    duration = info.get("duration")

    print(f"\nTitle: {title}")

    if duration:
        minutes = duration // 60
        seconds = duration % 60
        print(f"Duration: {minutes}:{seconds:02d}")

    qualities = get_qualities(info)

    if not qualities:
        print("\nNo video qualities found.")
        return

    print("\nAvailable qualities:")

    for i, quality in enumerate(qualities, start=1):
        print(f"{i}. {quality}p")

    while True:
        choice = input("\nChoose a quality: ").strip()

        try:
            choice = int(choice)

            if 1 <= choice <= len(qualities):
                selected_quality = qualities[choice - 1]
                break

            print("Invalid choice.")

        except ValueError:
            print("Please enter a number.")

    print(f"\nDownloading {selected_quality}p...")
    print("Please wait...\n")

    try:
        download_video(url, selected_quality)
    except Exception as e:
        print("\nDownload failed:")
        print(e)
        return

    print("\nDownload complete!")


if __name__ == "__main__":
    main()
