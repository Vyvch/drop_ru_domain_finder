import asyncio
import json
import os
import threading
import time
import urllib.request
import pytest
from PIL import Image, ImageChops, ImageStat

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "visual_output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROTO_PATH = "file:///" + os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "ITMOv2", "practices", "practice_08", "prototype", "index.html"
)).replace("\\", "/")

def is_server_running(url="http://127.0.0.1:8000"):
    try:
        with urllib.request.urlopen(url, timeout=1) as res:
            return res.status == 200
    except Exception:
        return False

@pytest.fixture(scope="session", autouse=True)
def ensure_server():
    if is_server_running():
        yield
        return

    import uvicorn
    config = uvicorn.Config("api:app", host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(40):
        if is_server_running():
            break
        time.sleep(0.15)
    yield

def compute_similarity(img1_path, img2_path, diff_out_path=None):
    im1 = Image.open(img1_path).convert("RGB")
    im2 = Image.open(img2_path).convert("RGB")

    w = min(im1.width, im2.width)
    h = min(im1.height, im2.height)
    c1 = im1.crop((0, 0, w, h))
    c2 = im2.crop((0, 0, w, h))

    diff = ImageChops.difference(c1, c2)
    if diff_out_path:
        diff.save(diff_out_path)

    # Pixel difference counting (threshold > 20)
    diff_pixels = 0
    try:
        pixel_iter = diff.get_flattened_data()
    except AttributeError:
        pixel_iter = diff.getdata()
    for px in pixel_iter:
        if (isinstance(px, (int, float)) and px > 20) or (isinstance(px, tuple) and max(px) > 20):
            diff_pixels += 1
    total_pixels = w * h
    mismatch_ratio = (diff_pixels / total_pixels) * 100.0
    return 100.0 - mismatch_ratio, mismatch_ratio

class TestVisualRegressionPrototypeMatch:
    """Automated visual screenshot tests comparing Live App against Prototype."""

    def test_top20_row_visual_fidelity(self):
        """Top-20 row visual similarity >= 92% compared to prototype."""
        from playwright.async_api import async_playwright

        async def run():
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                
                # 1. Prototype Top-20 row
                p_page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await p_page.goto(PROTO_PATH)
                await p_page.click("#tab-top-btn")
                await p_page.wait_for_timeout(400)
                p_row = await p_page.query_selector("#section-top tbody tr:first-child")
                p_path = os.path.join(OUTPUT_DIR, "proto_top_row.png")
                await p_row.screenshot(path=p_path)
                await p_page.close()

                # 2. Real App Top-20 row (with identical domain data for pixel fidelity)
                r_page = await browser.new_page(viewport={"width": 1280, "height": 800})
                mock_top = [{
                    "domain": "market-cloud.ru",
                    "date": "2026-11-23",
                    "reason": "Премиальный двухсловный домен в категории B2B SaaS и облачной электронной коммерции. Высокий потенциал прямого брендинга для платформ маркетплейс-интеграций.",
                    "whois": json.dumps({
                        "registrar": "RU-CENTER-RU",
                        "creation_date": "2017-04-10",
                        "status": "REGISTERED, DELEGATED"
                    })
                }]
                await r_page.route("**/api/top*", lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(mock_top)
                ))
                await r_page.goto("http://127.0.0.1:8000")
                await r_page.click("#tab-btn-top")
                await r_page.wait_for_selector("#top-body tr")
                await r_page.wait_for_timeout(400)
                r_row = await r_page.query_selector("#top-body tr:first-child")
                r_path = os.path.join(OUTPUT_DIR, "real_top_row.png")
                await r_row.screenshot(path=r_path)
                await r_page.close()

                await browser.close()

        asyncio.run(run())
        p_path = os.path.join(OUTPUT_DIR, "proto_top_row.png")
        r_path = os.path.join(OUTPUT_DIR, "real_top_row.png")
        diff_path = os.path.join(OUTPUT_DIR, "diff_top_row.png")
        similarity, mismatch = compute_similarity(p_path, r_path, diff_path)
        print(f"\n[Visual Test] Top-20 Row Match: {similarity:.2f}% (Mismatch: {mismatch:.2f}%)")
        assert similarity >= 92.0, f"Top-20 row visual similarity {similarity:.2f}% is below 92%"

    def test_top20_table_visual_fidelity(self):
        """Top-20 table visual similarity >= 92% compared to prototype."""
        p_path = os.path.join(OUTPUT_DIR, "proto_top_table.png")
        r_path = os.path.join(OUTPUT_DIR, "real_top_table.png")
        diff_path = os.path.join(OUTPUT_DIR, "diff_top_table.png")
        if not os.path.exists(p_path) or not os.path.exists(r_path):
            pytest.skip("Top table screenshots not yet generated")
        similarity, mismatch = compute_similarity(p_path, r_path, diff_path)
        print(f"\n[Visual Test] Top-20 Table Match: {similarity:.2f}% (Mismatch: {mismatch:.2f}%)")
        assert similarity >= 92.0, f"Top-20 table visual similarity {similarity:.2f}% is below 92%"

    def test_search_filter_bar_visual_fidelity(self):
        """Search and filter sticky bar visual similarity >= 92%."""
        p_path = os.path.join(OUTPUT_DIR, "proto_search.png")
        r_path = os.path.join(OUTPUT_DIR, "real_search.png")
        diff_path = os.path.join(OUTPUT_DIR, "diff_search.png")
        if not os.path.exists(p_path) or not os.path.exists(r_path):
            pytest.skip("Search screenshots not yet generated")
        similarity, mismatch = compute_similarity(p_path, r_path, diff_path)
        print(f"\n[Visual Test] Search Bar Match: {similarity:.2f}% (Mismatch: {mismatch:.2f}%)")
        assert similarity >= 92.0, f"Search bar visual similarity {similarity:.2f}% is below 92%"

    def test_whois_drawer_visual_fidelity(self):
        """WHOIS slide-over drawer visual similarity >= 90%."""
        p_path = os.path.join(OUTPUT_DIR, "proto_drawer.png")
        r_path = os.path.join(OUTPUT_DIR, "real_drawer.png")
        diff_path = os.path.join(OUTPUT_DIR, "diff_drawer.png")
        if not os.path.exists(p_path) or not os.path.exists(r_path):
            pytest.skip("Drawer screenshots not yet generated")
        similarity, mismatch = compute_similarity(p_path, r_path, diff_path)
        print(f"\n[Visual Test] WHOIS Drawer Match: {similarity:.2f}% (Mismatch: {mismatch:.2f}%)")
        assert similarity >= 90.0, f"Drawer visual similarity {similarity:.2f}% is below 90%"
