# Menuto

Menuto giúp cá nhân và hộ gia đình lên kế hoạch ăn uống, mua sắm và sử dụng thực phẩm theo ngân sách, mục tiêu dinh dưỡng và đồ đang có.

**Trạng thái: khung repository và tài liệu ban đầu — chưa có ứng dụng chạy được.**

## Nguồn chuẩn

[Đặc tả phát triển V1](docs/MENUTO_DEVELOPMENT_SPEC_V1.md) là nguồn chuẩn (source of truth) cho phạm vi, kiến trúc, dữ liệu, Planner V4 và tiêu chí hoàn thành. Tài liệu phụ phải dẫn về đặc tả; nếu có mâu thuẫn, làm rõ và cập nhật nguồn chuẩn trước khi triển khai.

Menuto là sản phẩm mới. Smart Menu là đồ án tham khảo; không kế thừa nguyên codebase hoặc lịch sử Git. Chỉ chuyển từng ý tưởng, tình huống kiểm thử hoặc module phù hợp sau khi rà soát theo mục 22 của đặc tả.

## Cấu trúc

```text
apps/
  web/                  Giao diện web/PWA, hiện chỉ có file giữ chỗ
  api/                  Backend/API, hiện chỉ có file giữ chỗ
data/
  seeds/                Dữ liệu khởi tạo có nguồn gốc và được duyệt
  imports/              Dữ liệu nhập tại máy, mặc định không đưa lên Git
tests/
  benchmark/            Ma trận tình huống; chưa có harness hoặc kết quả
  integration/          Chỗ cho kiểm thử tích hợp sau này
docs/
  MENUTO_DEVELOPMENT_SPEC_V1.md
  adr/                  Danh mục quyết định kiến trúc cần hoàn thiện
  product/              Ranh giới domain và lộ trình
  api/                  Chỗ cho hợp đồng API sau này
```

## Bắt đầu từ đâu?

1. Đọc [đặc tả V1](docs/MENUTO_DEVELOPMENT_SPEC_V1.md), nhất là mục 5, 6, 8–11 và 20–24.
2. Xem [ranh giới domain](docs/product/DOMAIN_BOUNDARIES.md), [danh mục ADR](docs/adr/README.md) và [lộ trình](docs/product/ROADMAP.md).
3. Theo [hướng dẫn đóng góp](CONTRIBUTING.md) khi bắt đầu triển khai; xem [chiến lược kiểm thử](tests/README.md) và [ma trận benchmark](tests/benchmark/README.md).

Chưa có lệnh cài đặt, chạy ứng dụng, migration hay test suite. Không cần cài framework hoặc cơ sở dữ liệu để đọc và sử dụng khung này.

## Thứ tự phát triển

| Mốc | Kết quả theo đặc tả | Trạng thái |
| --- | --- | --- |
| Milestone 0 | Foundation: ADR, thuật ngữ, quy ước, fixtures benchmark | Mới khởi tạo một phần; chưa hoàn tất |
| Milestone 1 | Identity/household, catalog/recipe, retail, inventory và chất lượng dữ liệu | Chưa triển khai |
| Milestone 2 | Planner V4, validator độc lập và benchmark/reference solver | Chưa triển khai |
| Milestone 3 | Onboarding, generate/swap/regenerate, Shop, Today và AI có giới hạn | Chưa triển khai |
| Milestone 4 | Security/privacy, vận hành, hiệu năng và điều kiện phát hành | Chưa triển khai |

Khung này chưa có API, schema cơ sở dữ liệu, dữ liệu bán lẻ, thuật toán, bộ cài phụ thuộc hay CI build ứng dụng.

## Bản tham khảo tại máy

Trong workspace hiện tại, thư mục `smart-menu/` và file đặc tả ở thư mục gốc được giữ nguyên nhưng không thuộc Git của Menuto. Bản đặc tả được quản lý trên Git chỉ nằm trong `docs/`; bản gốc tại máy chỉ để đối chiếu. Những bản tham khảo tại máy này không có khi clone repository.

Repository: [thedusk4203/Menuto](https://github.com/thedusk4203/Menuto).
