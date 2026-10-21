import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { getHealth } from "./api";
import "./style.css";

function App() {
  const [connection, setConnection] = useState("Đang kiểm tra kết nối…");
  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then(
      () => setConnection("Dịch vụ nền đã kết nối."),
      (error: unknown) => {
        if (!controller.signal.aborted) setConnection(
          error instanceof Error ? error.message : "Chưa kết nối được dịch vụ.",
        );
      },
    );
    return () => controller.abort();
  }, []);
  return <main>
    <p className="brand">Menuto</p>
    <h1>Nền tảng cho một tuần ăn uống dễ thực hiện.</h1>
    <p>Project đang ở giai đoạn xây dựng nền theo đặc tả V1.2.</p>
    <section aria-labelledby="status-title">
      <h2 id="status-title">Trạng thái phát triển</h2>
      <p role="status">{connection}</p>
      <p>Planner, kế hoạch ăn, mua sắm và quản lý bếp chưa được triển khai.</p>
    </section>
    <p className="note">Đây là giao diện khởi tạo, chưa phải ứng dụng meal planner hoàn chỉnh.</p>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App />);
