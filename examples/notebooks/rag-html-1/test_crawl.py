from dpk_connector import crawl, shutdown


def main():
    """
    An example of running crawler.
    """

    def on_downloaded(url: str, body: bytes, headers: dict) -> None:
        # print(f"url: {url}, headers: {headers}, body: {body[:64]}")
        print(f"url: {url}")

    user_agent = "Mozilla/5.0 (X11; Linux i686; rv:125.0) Gecko/20100101 Firefox/125.0"

    crawl(
        ["https://thealliance.ai/"],
        on_downloaded,
        user_agent=user_agent,
        depth_limit=1,
        subdomain_focus=True,
    )  # blocking call

    shutdown()


if __name__ == "__main__":
    main()
