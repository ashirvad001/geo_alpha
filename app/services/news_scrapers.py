"""
News scrapers for Indian financial news sources.

Scrapers:
- EconomicTimesScraper: BeautifulSoup + httpx for ET Markets
- MoneycontrolScraper: Selenium for JS-heavy pages
- BusinessStandardScraper: BeautifulSoup + httpx for BS Markets

Each scraper produces RawArticle objects stored in MongoDB.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════

@dataclass
class RawArticle:
    """Represents a scraped news article before NLP processing."""
    url: str
    title: str
    body: str
    source: str
    publish_time: datetime | None = None
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stock_mentions: list[str] = field(default_factory=list)

    def to_mongo_doc(self) -> dict:
        """Convert to MongoDB document."""
        return {
            "url": self.url,
            "title": self.title,
            "body": self.body,
            "source": self.source,
            "publish_time": self.publish_time,
            "scraped_at": self.scraped_at,
            "stock_mentions": self.stock_mentions,
            "sentiment": None,  # Filled by FinBERT pipeline
            "processed": False,
        }


# ═══════════════════════════════════════════════════════
# Base Scraper
# ═══════════════════════════════════════════════════════

class BaseNewsScraper(ABC):
    """Abstract base for all news scrapers."""

    SOURCE_NAME: str = "unknown"
    MAX_ARTICLES: int = 30

    def __init__(self):
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    @abstractmethod
    async def scrape(self) -> list[RawArticle]:
        """Scrape articles from this source."""
        ...

    def _clean_text(self, text: str) -> str:
        """Strip extra whitespace from scraped text."""
        return " ".join(text.split()).strip()


# ═══════════════════════════════════════════════════════
# Economic Times Scraper
# ═══════════════════════════════════════════════════════

class EconomicTimesScraper(BaseNewsScraper):
    """
    Scrapes Economic Times Markets section.
    Uses httpx + BeautifulSoup (server-rendered pages).
    """

    SOURCE_NAME = "economic_times"
    BASE_URL = "https://economictimes.indiatimes.com"
    MARKETS_URL = f"{BASE_URL}/markets/stocks/news"

    async def scrape(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        try:
            async with httpx.AsyncClient(
                headers=self._headers,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                resp = await client.get(self.MARKETS_URL)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # ET uses various article containers
            story_links = soup.select("div.eachStory a, div.story_list a, a.flt")
            seen_urls: set[str] = set()

            for link in story_links[: self.MAX_ARTICLES * 2]:
                href = link.get("href", "")
                if not href or "/articleshow/" not in href:
                    continue
                full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                title = self._clean_text(link.get_text())
                if not title or len(title) < 10:
                    continue

                articles.append(
                    RawArticle(
                        url=full_url,
                        title=title,
                        body="",  # Body fetched on-demand or by worker
                        source=self.SOURCE_NAME,
                    )
                )
                if len(articles) >= self.MAX_ARTICLES:
                    break

            # Fetch article bodies for top articles
            await self._enrich_bodies(articles[:10])

        except Exception as e:
            logger.error(f"EconomicTimesScraper failed: {e}")

        logger.info(f"ET scraped {len(articles)} articles")
        return articles

    async def _enrich_bodies(self, articles: list[RawArticle]) -> None:
        """Fetch full article text for a subset of articles."""
        async with httpx.AsyncClient(
            headers=self._headers,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            for article in articles:
                try:
                    resp = await client.get(article.url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # ET article body selectors
                        body_div = soup.select_one(
                            "div.artText, div.Normal, div.story_content"
                        )
                        if body_div:
                            article.body = self._clean_text(body_div.get_text())
                except Exception as e:
                    logger.debug(f"Failed to fetch ET article body: {e}")


# ═══════════════════════════════════════════════════════
# Moneycontrol Scraper (Selenium for JS)
# ═══════════════════════════════════════════════════════

class MoneycontrolScraper(BaseNewsScraper):
    """
    Scrapes Moneycontrol news — uses Selenium for JS-rendered content.
    Falls back to httpx if Selenium is unavailable.
    """

    SOURCE_NAME = "moneycontrol"
    MARKETS_URL = "https://www.moneycontrol.com/news/business/markets/"

    async def scrape(self) -> list[RawArticle]:
        # Try Selenium first for JS-rendered content
        articles = self._scrape_with_selenium()
        if articles:
            logger.info(f"Moneycontrol (Selenium) scraped {len(articles)} articles")
            return articles

        # Fallback to httpx for basic HTML
        return await self._scrape_with_httpx()

    def _scrape_with_selenium(self) -> list[RawArticle]:
        """Attempt Selenium-based scraping."""
        articles: list[RawArticle] = []
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"user-agent={self._headers['User-Agent']}")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)

            try:
                driver.get(self.MARKETS_URL)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.clearfix"))
                )

                items = driver.find_elements(By.CSS_SELECTOR, "li.clearfix")
                seen_urls: set[str] = set()

                for item in items[: self.MAX_ARTICLES]:
                    try:
                        link_el = item.find_element(By.CSS_SELECTOR, "h2 a, a.title")
                        title = link_el.text.strip()
                        url = link_el.get_attribute("href")

                        if not url or url in seen_urls or not title:
                            continue
                        seen_urls.add(url)

                        # Try to get snippet
                        body = ""
                        try:
                            p_el = item.find_element(By.CSS_SELECTOR, "p")
                            body = p_el.text.strip()
                        except Exception:
                            pass

                        articles.append(
                            RawArticle(
                                url=url,
                                title=title,
                                body=body,
                                source=self.SOURCE_NAME,
                            )
                        )
                    except Exception:
                        continue
            finally:
                driver.quit()

        except ImportError:
            logger.warning("Selenium not available, falling back to httpx")
        except Exception as e:
            logger.error(f"MoneycontrolScraper Selenium failed: {e}")

        return articles

    async def _scrape_with_httpx(self) -> list[RawArticle]:
        """Fallback httpx-based scraping."""
        articles: list[RawArticle] = []
        try:
            async with httpx.AsyncClient(
                headers=self._headers,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                resp = await client.get(self.MARKETS_URL)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("li.clearfix")
            seen_urls: set[str] = set()

            for item in items[: self.MAX_ARTICLES]:
                link = item.select_one("h2 a, a.title")
                if not link:
                    continue
                url = link.get("href", "")
                title = self._clean_text(link.get_text())
                if not url or not title or url in seen_urls:
                    continue
                seen_urls.add(url)

                body = ""
                p_tag = item.select_one("p")
                if p_tag:
                    body = self._clean_text(p_tag.get_text())

                articles.append(
                    RawArticle(
                        url=url,
                        title=title,
                        body=body,
                        source=self.SOURCE_NAME,
                    )
                )
        except Exception as e:
            logger.error(f"MoneycontrolScraper httpx failed: {e}")

        logger.info(f"Moneycontrol (httpx) scraped {len(articles)} articles")
        return articles


# ═══════════════════════════════════════════════════════
# Business Standard Scraper
# ═══════════════════════════════════════════════════════

class BusinessStandardScraper(BaseNewsScraper):
    """
    Scrapes Business Standard Markets section.
    Uses httpx + BeautifulSoup (mostly server-rendered).
    """

    SOURCE_NAME = "business_standard"
    MARKETS_URL = "https://www.business-standard.com/markets/news"

    async def scrape(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        try:
            async with httpx.AsyncClient(
                headers=self._headers,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                resp = await client.get(self.MARKETS_URL)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # BS article selectors
            links = soup.select(
                "div.listing-txt a, div.cardBasicTitle a, h2 a, .story-title a"
            )
            seen_urls: set[str] = set()

            for link in links[: self.MAX_ARTICLES * 2]:
                href = link.get("href", "")
                if not href:
                    continue
                full_url = (
                    href
                    if href.startswith("http")
                    else f"https://www.business-standard.com{href}"
                )
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                title = self._clean_text(link.get_text())
                if not title or len(title) < 10:
                    continue

                articles.append(
                    RawArticle(
                        url=full_url,
                        title=title,
                        body="",
                        source=self.SOURCE_NAME,
                    )
                )
                if len(articles) >= self.MAX_ARTICLES:
                    break

            # Enrich top articles with body text
            await self._enrich_bodies(articles[:10])

        except Exception as e:
            logger.error(f"BusinessStandardScraper failed: {e}")

        logger.info(f"BS scraped {len(articles)} articles")
        return articles

    async def _enrich_bodies(self, articles: list[RawArticle]) -> None:
        """Fetch full article text for a subset of articles."""
        async with httpx.AsyncClient(
            headers=self._headers,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            for article in articles:
                try:
                    resp = await client.get(article.url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        body_div = soup.select_one(
                            "div.story-content, div.p-content, span.p-content"
                        )
                        if body_div:
                            article.body = self._clean_text(body_div.get_text())
                except Exception as e:
                    logger.debug(f"Failed to fetch BS article body: {e}")


# ═══════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════

ALL_SCRAPERS: list[type[BaseNewsScraper]] = [
    EconomicTimesScraper,
    MoneycontrolScraper,
    BusinessStandardScraper,
]


async def scrape_all_sources() -> list[RawArticle]:
    """
    Run all scrapers concurrently (with error isolation).
    Returns combined list of RawArticle objects.
    """
    import asyncio

    all_articles: list[RawArticle] = []

    async def _run_scraper(scraper_cls: type[BaseNewsScraper]) -> list[RawArticle]:
        try:
            scraper = scraper_cls()
            return await scraper.scrape()
        except Exception as e:
            logger.error(f"Scraper {scraper_cls.SOURCE_NAME} failed: {e}")
            return []

    tasks = [_run_scraper(cls) for cls in ALL_SCRAPERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Scraper returned exception: {result}")

    logger.info(f"Total scraped articles: {len(all_articles)}")
    return all_articles


async def store_articles_mongo(articles: list[RawArticle]) -> int:
    """
    Store scraped articles in MongoDB with deduplication by URL.

    Returns: number of newly inserted articles.
    """
    from app.database import get_mongo_db

    db = get_mongo_db()
    collection = db["raw_news_articles"]

    # Ensure index for deduplication
    await collection.create_index("url", unique=True)
    await collection.create_index("scraped_at")
    await collection.create_index("processed")
    await collection.create_index("stock_mentions")

    inserted = 0
    for article in articles:
        try:
            await collection.insert_one(article.to_mongo_doc())
            inserted += 1
        except Exception:
            # Duplicate URL — skip
            pass

    logger.info(f"Stored {inserted}/{len(articles)} new articles in MongoDB")
    return inserted
