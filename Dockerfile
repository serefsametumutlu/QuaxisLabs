# Bilanço Radar - Railway (veya herhangi bir Docker destekli platform) icin.
# playwright>=1.45 kart PNG'lerini uretmek icin headless Chromium calistiriyor
# (bkz. src/render/card.py) -- "playwright install --with-deps chromium" bu
# yuzden zorunlu, sadece "pip install playwright" tarayiciyi INDIRMEZ.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# data/ (SQLite DB, loglar, uretilen kart PNG'leri, KAP/sektor onbellegi)
# Railway'de kalici bir Volume olarak buraya baglanmali (bkz. DEPLOY.md) --
# aksi halde her yeniden deploy'da/restart'ta SIFIRLANIR. config.py zaten
# klasoru yoksa kendisi olusturuyor, bu yuzden bos bir volume ile de calisir.
VOLUME ["/app/data"]

CMD ["python", "main.py"]
