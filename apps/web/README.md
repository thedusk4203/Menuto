# Web scaffold

React + TypeScript + Vite. Chỉ có trang trạng thái foundation và gọi health API thật; chưa có onboarding hoặc nghiệp vụ.

```powershell
npm ci
npm run dev
```

Chạy tại `apps/web`; mở http://127.0.0.1:5173. Backend tại http://127.0.0.1:8000 được proxy qua `/api` khi dev. `npm run build` kiểm tra kiểu và đóng gói. Khi deploy cần same-origin routing `/api` đến backend; chưa có production deployment.
