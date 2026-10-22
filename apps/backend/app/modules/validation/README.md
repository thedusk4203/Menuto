# Independent validation — namespace V1.3

ADR-010, INV-015..021. Chưa có ValidationOrchestrator hoặc production validator.

Interface sẽ nhận immutable ValidationSubjectSnapshot và trả structured findings/derived facts/trace/hashes, không search, optimize hoặc repair. Ba đường kiểm chứng: root contract guards, primitive arithmetic recomputation, global conservation + chronological replay.

Chỉ import domain contracts và shared primitives. Không import planning.public, constraint builders, candidate generators, objectives hoặc OR-Tools; contracts cũng không được vòng qua nội bộ domain. PRECOMMIT gate intent; POSTFACT diagnostic reality. Luật import được CI kiểm tra, không thay test semantics hoặc kiểm soát runtime/SQL.
