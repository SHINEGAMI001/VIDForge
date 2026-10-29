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


def resolve_subtitle_lang(lang, info):
    """Prefer manual subtitles, then the original automatic-caption track."""
    manual = info.get("subtitles") or {}
    if lang in manual:
        return lang

    auto = info.get("automatic_captions") or {}
    if lang.endswith("-orig"):
        return lang

    original = f"{lang}-orig"
    if original in auto:
        return original

    return lang


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
        result = ydl.download([url])

    if result != 0:
        raise RuntimeError("Video download failed.")


def download_subtitles(url, sub):
    options = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [sub],
        "subtitlesformat": "vtt/srt/best",
        "sleep_interval_subtitles": 5,
        "outtmpl": "downloads/%(title)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.download([url])

    if result != 0:
        raise RuntimeError("Subtitle download failed.")


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

    ## Get video qualities
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


    ## Get video subtitles
    manual_sub = list((info.get("subtitles") or {}).keys())
    auto_sub = list((info.get("automatic_captions") or {}).keys())
    langs = set(manual_sub) | set(auto_sub)

    # yt-dlp exposes "<lang>-orig" for the original automatic track.
    # Show it as "<lang>" and resolve it when downloading.
    display_langs = set()
    for lang in langs:
        if lang.endswith("-orig"):
            display_langs.add(lang[:-5])
        else:
            display_langs.add(lang)

    selected_sub = None

    if display_langs:
        prefer_subs = ["en", "fr", "ar", "es"]
        preferred = [lang for lang in prefer_subs if lang in display_langs]
        advanced = sorted(lang for lang in display_langs if lang not in prefer_subs)

        print("0. No subtitles")

        for i, sub in enumerate(preferred, start=1):
            print(f"{i}. {sub}")

        if advanced:
            print(f"{len(preferred) + 1}. more subtitles")

        while True:
            choice = input("\nChoose a language (0 = no subtitles): ").strip()

            if choice.lower() in {"0", "no", "none", "skip"}:
                selected_sub = None
                break

            try:
                choice = int(choice)

                if 1 <= choice <= len(preferred):
                    selected_sub = preferred[choice - 1]
                    break

                elif choice == len(preferred) + 1 and advanced:
                    for i, sub in enumerate(advanced, start=1):
                        print(f"{i}. {sub}")

                    adv_choice = input(
                        "\nChoose a language (0 = no subtitles): "
                    ).strip()

                    if adv_choice.lower() in {"0", "no", "none", "skip"}:
                        selected_sub = None
                        break

                    try:
                        adv_choice = int(adv_choice)
                        if 1 <= adv_choice <= len(advanced):
                            selected_sub = advanced[adv_choice - 1]
                            break  # Exit the loop
                        else:
                            print("Invalid Choice")

                    except ValueError:
                        print("\nPlease enter a number")

                else:
                    print("Invalid Choice")

            except ValueError:
                print("\nPlease enter a number")
    else:
        print("\nNo video subtitles found")

    download_lang = (
        resolve_subtitle_lang(selected_sub, info) if selected_sub else None
    )

    print(f"\nDownloading {selected_quality}p video...")
    print("Please wait...\n")

    try:
        download_video(url, selected_quality)
    except Exception as e:
        print("\nDownload failed:")
        print(e)
        return

    print("\nVideo download complete!")

    if download_lang:
        print(f"\nDownloading {selected_sub} subtitle...")
        if download_lang != selected_sub:
            print(f"Using original automatic track: {download_lang}")
        try:
            download_subtitles(url, download_lang)
        except Exception as e:
            print("\nVideo downloaded successfully, but the subtitle download failed:")
            print(e)
            print("YouTube may be rate-limiting subtitle requests.")
            print("The video is already saved. Choose 0 (No subtitles) next time to skip subtitles.")
            return

    print("\nDownload complete!")


if __name__ == "__main__":
    main()
