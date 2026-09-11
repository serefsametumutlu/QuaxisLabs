Terminal 1 — Backend (FastAPI):
cd "C:\Users\Samet\Desktop\Teknik Analiz"
python -m uvicorn web.backend.main:app --reload --port 8000

Terminal 2 — Frontend (Next.js):
cd "C:\Users\Samet\Desktop\Teknik Analiz\web\frontend"
npm run dev

Sonra tarayıcıdan http://localhost:3000 adresini aç — tarama/grafik/stratejiler arayüzü orada.