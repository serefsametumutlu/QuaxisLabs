"""SQLite sonuç deposu (`outputs/results.db`) + tam IndicatorResult JSON
klasörü (`outputs/results/{run_id}/`).

ŞEMA DONUK — Bilanço Radar (kardeş proje) ile `symbol` üzerinden join
edilecek; alan adlarını DEĞİŞTİRME (yeni alan eklemek serbest, mevcut
alanı yeniden adlandırmak/kaldırmak DEĞİL).

`signals` tablosunun `pattern_id` alanı: her indikatör kendi payload'ında
farklı bir "hangi aday/olay" anahtarı taşır (harmonikler `pattern_id`,
SwingFibABCD `triple_id`, diğerleri yalnızca `event`) — bkz. `_pattern_key()`
bunları TEK bir alana normalize eder. Bu, PK'nin (run_id, symbol, timeframe,
indicator, pattern_id, state, bar_time) parçası olduğu için ÖNEMLİ: aynı
anahtar ikinci kez yazılırsa (aynı çalıştırmada teorik bir çakışma)
INSERT OR REPLACE ile üzerine yazılır — sessizce kaybolma YOK, ama gerçek
bir çakışma olursa en son yazan kazanır (nadir, dokümante edilmiş sınırlama).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tlab.core.types import IndicatorResult, Signal

DEFAULT_DB_PATH = Path("outputs") / "results.db"
DEFAULT_JSON_ROOT = Path("outputs") / "results"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    market TEXT NOT NULL,
    timeframes TEXT NOT NULL,
    universe_size INTEGER NOT NULL,
    indicators_json TEXT NOT NULL,
    git_sha TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    indicator TEXT NOT NULL,
    params_hash TEXT NOT NULL,
    bar_time TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    direction TEXT NOT NULL,
    state TEXT NOT NULL,
    score REAL NOT NULL,
    pattern_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol, timeframe, indicator, pattern_id, state, bar_time)
);

CREATE TABLE IF NOT EXISTS states (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    indicator TEXT NOT NULL,
    last_state_json TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol, timeframe, indicator)
);

CREATE TABLE IF NOT EXISTS data_quality (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    status TEXT NOT NULL,
    report_json TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol, timeframe)
);
"""


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    started_at: str
    finished_at: str | None
    market: str
    timeframes: list[str]
    universe_size: int
    indicator_names: list[str]
    git_sha: str | None
    status: str


@dataclass(frozen=True)
class SymbolIndicatorRun:
    """engine.run()'dan persist()'e verilen tek bir (symbol veya y/x çifti,
    timeframe, indikatör) sonucu — bkz. scanner/engine.py::IndicatorRunResult
    (bu, o dataclass'ın SQLite'a yazılabilir izdüşümüdür)."""

    symbol: str
    market: str
    timeframe: str
    indicator: str
    params_hash: str
    result: IndicatorResult | None
    error: str | None


@dataclass(frozen=True)
class DataQualityRecord:
    symbol: str
    timeframe: str
    status: str
    report: dict[str, Any]


@dataclass(frozen=True)
class DiffReport:
    new_signals: list[dict] = field(default_factory=list)
    transitions: list[dict] = field(default_factory=list)
    missing_signals: list[dict] = field(default_factory=list)

    @property
    def has_repaint_alarm(self) -> bool:
        return len(self.missing_signals) > 0


def _pattern_key(signal: Signal) -> str:
    payload = signal.payload
    return str(
        payload.get("pattern_id")
        or payload.get("triple_id")
        or payload.get("event")
        or "signal"
    )


class ResultsStore:
    def __init__(
        self, db_path: Path = DEFAULT_DB_PATH, json_root: Path = DEFAULT_JSON_ROOT
    ) -> None:
        self.db_path = db_path
        self.json_root = json_root
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ResultsStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- yazma -----------------------------------------------------------

    def start_run(self, run: RunRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO runs "
            "(run_id, started_at, finished_at, market, timeframes, universe_size, "
            " indicators_json, git_sha, status) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                run.run_id, run.started_at, run.finished_at, run.market,
                json.dumps(run.timeframes), run.universe_size,
                json.dumps(run.indicator_names), run.git_sha, run.status,
            ),
        )
        self._conn.commit()

    def finish_run(self, run_id: str, finished_at: str, status: str) -> None:
        self._conn.execute(
            "UPDATE runs SET finished_at = ?, status = ? WHERE run_id = ?",
            (finished_at, status, run_id),
        )
        self._conn.commit()

    def persist(self, run_id: str, results: list[SymbolIndicatorRun]) -> None:
        for item in results:
            if item.error is not None:
                self._conn.execute(
                    "INSERT OR REPLACE INTO signals "
                    "(run_id, symbol, market, timeframe, indicator, params_hash, bar_time, "
                    " detected_at, direction, state, score, pattern_id, payload_json) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        run_id, item.symbol, item.market, item.timeframe, item.indicator,
                        item.params_hash, "", "", "neutral", "error", 0.0, "error",
                        json.dumps({"error": item.error}, ensure_ascii=False),
                    ),
                )
                continue

            assert item.result is not None
            for signal in item.result.signals:
                self._conn.execute(
                    "INSERT OR REPLACE INTO signals "
                    "(run_id, symbol, market, timeframe, indicator, params_hash, bar_time, "
                    " detected_at, direction, state, score, pattern_id, payload_json) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        run_id, item.symbol, item.market, item.timeframe, item.indicator,
                        item.params_hash, signal.bar_time.isoformat(),
                        signal.detected_at.isoformat(),
                        signal.direction, signal.state, signal.score, _pattern_key(signal),
                        json.dumps(signal.payload, ensure_ascii=False, default=str),
                    ),
                )
            self._conn.execute(
                "INSERT OR REPLACE INTO states "
                "(run_id, symbol, timeframe, indicator, last_state_json) VALUES (?,?,?,?,?)",
                (
                    run_id, item.symbol, item.timeframe, item.indicator,
                    json.dumps(item.result.last_state, ensure_ascii=False, default=str),
                ),
            )
            self._write_json(run_id, item)
        self._conn.commit()

    def persist_data_quality(self, run_id: str, records: list[DataQualityRecord]) -> None:
        for rec in records:
            self._conn.execute(
                "INSERT OR REPLACE INTO data_quality "
                "(run_id, symbol, timeframe, status, report_json) VALUES (?,?,?,?,?)",
                (
                    run_id, rec.symbol, rec.timeframe, rec.status,
                    json.dumps(rec.report, ensure_ascii=False),
                ),
            )
        self._conn.commit()

    def _write_json(self, run_id: str, item: SymbolIndicatorRun) -> None:
        assert item.result is not None
        out_dir = self.json_root / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_symbol = item.symbol.replace("/", "-")
        out_path = out_dir / f"{safe_symbol}_{item.timeframe}_{item.indicator}.json"
        out_path.write_text(item.result.to_json(), encoding="utf-8")

    # -- okuma -------------------------------------------------------------

    def read_result(
        self, run_id: str, symbol: str, timeframe: str, indicator: str
    ) -> IndicatorResult | None:
        """`_write_json`'ın YAZDIĞI tam `IndicatorResult`'ı geri okur (Faz 8E
        `confluence.py`'nin ihtiyaç duyduğu Level/Box/Line geometrisi
        `signals` tablosunda YOK — yalnızca tam JSON dosyasında var). Dosya
        yoksa (o run'da bu indikatör bu sembolde HATA vermiş veya hiç
        koşulmamış) `None` döner, istisna fırlatmaz."""
        safe_symbol = symbol.replace("/", "-")
        path = self.json_root / run_id / f"{safe_symbol}_{timeframe}_{indicator}.json"
        if not path.exists():
            return None
        return IndicatorResult.from_json(path.read_text(encoding="utf-8"))

    def list_symbol_indicators(
        self, run_id: str, timeframe: str | None = None
    ) -> list[tuple[str, str, str]]:
        """O run'da BAŞARIYLA sonuç üretmiş (hatasız) (symbol, timeframe,
        indicator) üçlülerini döner — `states` tablosu yalnızca `persist()`'in
        `item.result is not None` dalında yazılır (bkz. `persist()`), bu
        yüzden hatalı koşular burada hiç görünmez."""
        if timeframe is not None:
            cur = self._conn.execute(
                "SELECT DISTINCT symbol, timeframe, indicator FROM states "
                "WHERE run_id = ? AND timeframe = ?",
                (run_id, timeframe),
            )
        else:
            cur = self._conn.execute(
                "SELECT DISTINCT symbol, timeframe, indicator FROM states WHERE run_id = ?",
                (run_id,),
            )
        return [(row[0], row[1], row[2]) for row in cur.fetchall()]

    def list_runs(self, market: str, status: str | None = None) -> list[str]:
        """market için run_id'leri, EN YENİDEN EN ESKİYE sıralı döner
        (`started_at` bazlı) — `eod.py`'nin "önceki run"u bulması için."""
        if status is not None:
            cur = self._conn.execute(
                "SELECT run_id FROM runs WHERE market = ? AND status = ? "
                "ORDER BY started_at DESC",
                (market, status),
            )
        else:
            cur = self._conn.execute(
                "SELECT run_id FROM runs WHERE market = ? ORDER BY started_at DESC",
                (market,),
            )
        return [row[0] for row in cur.fetchall()]

    def query(
        self,
        run_id: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        indicator: str | None = None,
        state: str | None = None,
    ) -> list[dict]:
        clauses, params = [], []
        for col, val in (
            ("run_id", run_id), ("symbol", symbol), ("timeframe", timeframe),
            ("indicator", indicator), ("state", state),
        ):
            if val is not None:
                clauses.append(f"{col} = ?")
                params.append(val)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = self._conn.execute(f"SELECT * FROM signals {where} ORDER BY bar_time", params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]

    def latest_run(self, market: str) -> str | None:
        cur = self._conn.execute(
            "SELECT run_id FROM runs WHERE market = ? AND status = 'completed' "
            "ORDER BY started_at DESC LIMIT 1",
            (market,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def get_run(self, run_id: str) -> RunRecord | None:
        cur = self._conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        raw = dict(zip(cols, row, strict=True))
        return RunRecord(
            run_id=raw["run_id"], started_at=raw["started_at"], finished_at=raw["finished_at"],
            market=raw["market"], timeframes=json.loads(raw["timeframes"]),
            universe_size=raw["universe_size"], indicator_names=json.loads(raw["indicators_json"]),
            git_sha=raw["git_sha"], status=raw["status"],
        )

    def diff(self, run_a: str, run_b: str) -> DiffReport:
        """run_a: ÖNCEKİ (baseline), run_b: SONRAKİ (yeni) koşu."""
        rows_a = self.query(run_id=run_a)
        rows_b = self.query(run_id=run_b)

        def key(r: dict) -> tuple:
            return (
                r["symbol"], r["timeframe"], r["indicator"],
                r["pattern_id"], r["state"], r["bar_time"],
            )

        def chain_key(r: dict) -> tuple:
            return (r["symbol"], r["timeframe"], r["indicator"], r["pattern_id"])

        keys_a = {key(r) for r in rows_a}
        keys_b = {key(r) for r in rows_b}

        new_signals = [r for r in rows_b if key(r) not in keys_a]
        missing_signals = [r for r in rows_a if key(r) not in keys_b]

        states_by_chain_a: dict[tuple, set[str]] = {}
        for r in rows_a:
            states_by_chain_a.setdefault(chain_key(r), set()).add(r["state"])

        transitions = []
        for r in rows_b:
            ck = chain_key(r)
            prior_states = states_by_chain_a.get(ck, set())
            if ck in states_by_chain_a and r["state"] not in prior_states:
                transitions.append({**r, "from_states": sorted(prior_states)})

        return DiffReport(
            new_signals=new_signals, transitions=transitions, missing_signals=missing_signals,
        )
