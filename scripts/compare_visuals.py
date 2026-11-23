import asyncio
import json
import os
from playwright.async_api import async_playwright
from PIL import Image, ImageChops, ImageStat

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "visual_output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROTO_PATH = "file:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ITMOv2", "practices", "practice_08", "prototype", "index.html")).replace("\\", "/")

def compute_similarity(img1_path, img2_path, diff_out_path=None):
    im1 = Image.open(img1_path).convert("RGB")
    im2 = Image.open(img2_path).convert("RGB")
    
    # Common bounding box
    w = min(im1.width, im2.width)
    h = min(im1.height, im2.height)
    c1 = im1.crop((0, 0, w, h))
    c2 = im2.crop((0, 0, w, h))
    
    diff = ImageChops.difference(c1, c2)
    if diff_out_path:
        diff.save(diff_out_path)
        
    stat = ImageStat.Stat(diff)
    diff_pixels = sum(1 for px in diff.getdata() if max(px) > 20)
    total_pixels = w * h
    mismatch_ratio = (diff_pixels / total_pixels) * 100
    similarity = 100.0 - mismatch_ratio
    return {
        "similarity": similarity,
        "mismatch_ratio": mismatch_ratio,
        "diff_pixels": diff_pixels,
        "total_pixels": total_pixels,
        "w": w,
        "h": h
    }

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Capture Prototype
        p_page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await p_page.goto(PROTO_PATH)
        await p_page.wait_for_timeout(300)
        
        # Proto Catalog View
        catalog_proto = await p_page.query_selector("#section-all")
        if catalog_proto:
            await catalog_proto.screenshot(path=os.path.join(OUTPUT_DIR, "proto_catalog.png"))
            
        # Proto Search Bar
        search_proto = await p_page.query_selector(".sticky")
        if search_proto:
            await search_proto.screenshot(path=os.path.join(OUTPUT_DIR, "proto_search.png"))
            
        # Proto Top-20
        await p_page.click("#tab-top-btn")
        await p_page.wait_for_timeout(400)
        top_table_proto = await p_page.query_selector("#section-top table")
        if top_table_proto:
            await top_table_proto.screenshot(path=os.path.join(OUTPUT_DIR, "proto_top_table.png"))
        top_row_proto = await p_page.query_selector("#section-top tbody tr:first-child")
        if top_row_proto:
            await top_row_proto.screenshot(path=os.path.join(OUTPUT_DIR, "proto_top_row.png"))
            
        # Proto Drawer
        await p_page.click("#tab-all-btn")
        await p_page.wait_for_timeout(300)
        await p_page.click(".domain-table-row:first-child")
        await p_page.wait_for_selector("#drawer-panel.open")
        await p_page.wait_for_timeout(400)
        drawer_proto = await p_page.query_selector("#drawer-panel")
        if drawer_proto:
            await drawer_proto.screenshot(path=os.path.join(OUTPUT_DIR, "proto_drawer.png"))
        await p_page.close()
        
        # 2. Capture Real App
        r_page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Mock /api/top to return market-cloud.ru so content is identical for exact pixel comparison
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
        await r_page.wait_for_selector(".domain-card")
        await r_page.wait_for_timeout(400)
        
        # Real Search Bar
        search_real = await r_page.query_selector(".sticky")
        if search_real:
            await search_real.screenshot(path=os.path.join(OUTPUT_DIR, "real_search.png"))
            
        # Real Top-20 (identical mocked data)
        await r_page.click("#tab-btn-top")
        await r_page.wait_for_selector("#top-body tr")
        await r_page.wait_for_timeout(400)
        top_table_real = await r_page.query_selector("#top-table")
        if top_table_real:
            await top_table_real.screenshot(path=os.path.join(OUTPUT_DIR, "real_top_table.png"))
        top_row_real = await r_page.query_selector("#top-body tr:first-child")
        if top_row_real:
            await top_row_real.screenshot(path=os.path.join(OUTPUT_DIR, "real_top_row.png"))
            
        # Real Drawer
        await r_page.click("#tab-btn-all")
        await r_page.wait_for_timeout(300)
        await r_page.click(".domain-card:first-child")
        await r_page.wait_for_selector("#domain-dialog[open]")
        await r_page.wait_for_timeout(400)
        drawer_real = await r_page.query_selector("#domain-dialog")
        if drawer_real:
            await drawer_real.screenshot(path=os.path.join(OUTPUT_DIR, "real_drawer.png"))
        await r_page.close()
        
        await browser.close()

def main():
    asyncio.run(capture_all())
    
    # Comparisons
    components = [
        ("top_row", "proto_top_row.png", "real_top_row.png"),
        ("top_table", "proto_top_table.png", "real_top_table.png"),
        ("drawer", "proto_drawer.png", "real_drawer.png"),
        ("search", "proto_search.png", "real_search.png"),
    ]
    
    results = {}
    for name, p_img, r_img in components:
        p_path = os.path.join(OUTPUT_DIR, p_img)
        r_path = os.path.join(OUTPUT_DIR, r_img)
        diff_path = os.path.join(OUTPUT_DIR, f"diff_{name}.png")
        if os.path.exists(p_path) and os.path.exists(r_path):
            res = compute_similarity(p_path, r_path, diff_path)
            results[name] = res
            print(f"[{name.upper()}] Similarity: {res['similarity']:.2f}% (Mismatch: {res['mismatch_ratio']:.2f}%)")
            
            # Make side by side combo
            im_p = Image.open(p_path).convert("RGB")
            im_r = Image.open(r_path).convert("RGB")
            im_d = Image.open(diff_path).convert("RGB")
            combo_w = im_p.width + im_r.width + im_d.width + 40
            combo_h = max(im_p.height, im_r.height, im_d.height)
            combo = Image.new("RGB", (combo_w, combo_h), (245, 245, 247))
            combo.paste(im_p, (0, 0))
            combo.paste(im_r, (im_p.width + 20, 0))
            combo.paste(im_d, (im_p.width + im_r.width + 40, 0))
            combo.save(os.path.join(OUTPUT_DIR, f"comparison_{name}.png"))
    
    with open(os.path.join(OUTPUT_DIR, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
