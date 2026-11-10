import fitz  # PyMuPDF

PDF = "data/samples/synthetic/sample_registry_synthetic.pdf"
doc = fitz.open(PDF)
page = doc[0]

# 1) 단어와 위치(bounding box)
words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)
print("pages:", len(doc), "| words on page 1:", len(words))
for x0, y0, x1, y1, w, *_ in words[:10]:
    print(f"({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})  {w}")

# 2) 금액 위치를 찾아서 빨간 상자로 그리기
hits = page.search_for("240,000,000")
print("found 240,000,000 at:", hits)
for r in hits:
    page.draw_rect(r, color=(1, 0, 0), width=1.5)
page.get_pixmap(dpi=110).save("report/img/step1_bbox_check.png")

# 3) 취소선 후보: 글자 중간을 지나가는 얇은 가로선
struck = []
for d in page.get_drawings():
    r = d["rect"]
    if r.height < 3 and r.width > 5:
        for x0, y0, x1, y1, w, *_ in words:
            h = y1 - y0
            mid = (r.y0 + r.y1) / 2
            if y0 + 0.3 * h <= mid <= y0 + 0.7 * h and r.x0 < x1 and r.x1 > x0:
                struck.append(w)
print("words with a line through them:", struck)
