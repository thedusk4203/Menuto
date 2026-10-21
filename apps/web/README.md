# Web scaffold

React + TypeScript + Vite, dùng @menuto/api-client sinh từ OpenAPI. Chỉ có trang foundation gọi health API, chưa có onboarding hoặc nghiệp vụ.

Từ root repository:

```powershell
npm ci
npm run contracts:check
npm run test:client
npm run build:web
npm run dev --workspace @menuto/web
```

Chỉ một lockfile npm tại root cho web và api-client. Mở http://127.0.0.1:5173; backend tại http://127.0.0.1:8000 được proxy qua /api khi dev. Khi deploy cần same-origin API routing; chưa có deployment production.
