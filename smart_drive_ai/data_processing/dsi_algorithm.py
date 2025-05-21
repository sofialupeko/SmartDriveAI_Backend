"""
Driver Style Index (DSI) – алгоритм из главы 6
(коэффициент доверия D, особый случай первого расчёта).

Совместимо с Python ≥ 3.7.
"""

from __future__ import annotations

import datetime
import enum
import math
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional, Sequence


# ────────────────── Коды категорий поездок ──────────────────

class TripClass(enum.IntEnum):
    SMOOTH = 0        # «плавный»
    MODERATE = 1      # «умеренный»
    AGGRESSIVE = 2    # «агрессивный»

    @classmethod
    def from_str(cls, label: str) -> "TripClass":
        mapping = {
            "smooth": cls.SMOOTH,
            "moderate": cls.MODERATE,
            "aggressive": cls.AGGRESSIVE,
        }
        try:
            return mapping[label.lower()]
        except KeyError as exc:
            raise ValueError(f"Неизвестная категория поездки: {label}") from exc


# ──────────────────────── Данные ────────────────────────────

@dataclass(frozen=True)
class Trip:
    timestamp: datetime.datetime
    category: TripClass


@dataclass(frozen=True)
class DSIParams:
    t_half: int = 30            # период полураспада (сутки)
    t_cut: int = 365            # горизонт отсечения (сутки)
    sigma_max: float = 0.8      # порог устойчивости
    n_ref: int = 5              # эталонное число поездок
    smooth_thresh: float = 0.67
    moderate_thresh: float = 1.33


@dataclass(frozen=True)
class DSIResult:
    dsi: float                  # значение индекса
    sigma: float                # взвешенное σ_c
    trust: float                # коэффициент доверия D (0…1)
    profile_class: TripClass    # итоговая категория
    trips_used: int             # учтённых поездок
    preliminary: bool           # True → оценка предварительная


# ────────────────── Вспомогательные функции ─────────────────

def _exp_weight(age_days: float, lam: float) -> float:
    """Экспоненциальная весовая функция w_i = e^{−λ t_i}."""
    return math.exp(-lam * age_days)


def _categorize(dsi: float, p: DSIParams) -> TripClass:
    """Дискретизация индекса DSI."""
    if dsi < p.smooth_thresh:
        return TripClass.SMOOTH
    elif dsi < p.moderate_thresh:
        return TripClass.MODERATE
    return TripClass.AGGRESSIVE


# ─────────────────── Основной алгоритм ──────────────────────

def compute_driver_style(
    trips: Sequence[Trip],
    *,
    previous_class: Optional[TripClass] = None,
    params: DSIParams = DSIParams(),
    now: Optional[datetime.datetime] = None,
) -> Optional[DSIResult]:
    """
    Рассчитывает DSI, коэффициент доверия D и категорию профиля.

    • `previous_class` — сохранённая ранее категория (None, если расчёт первый).
    • Возвращает None, если нет поездок в пределах T_cut.
    """

    trips
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - timedelta(days=params.t_cut)
    lam = math.log(2) / params.t_half

    recent: List[tuple[float, int, datetime.datetime]] = []  # (w_i, c_i, ts)

    # --- отбор поездок и веса ----------------------------------------------

    for trip in trips:
        if trip.timestamp < cutoff:
            continue
        age = now - trip.timestamp
        age_days = age.days + age.seconds / 86_400
        recent.append((_exp_weight(age_days, lam), int(trip.category), trip.timestamp))

    if not recent:
        return None  # совсем нет данных

    # --- индекс DSI ---------------------------------------------------------
    sum_w = sum(w for w, _, _ in recent)
    dsi = sum(w * c for w, c, _ in recent) / sum_w

    # --- взвешенная дисперсия и σ_c -----------------------------------------
    var = sum(w * (c - dsi) ** 2 for w, c, _ in recent) / sum_w
    sigma_c = math.sqrt(var)

    # --- коэффициент доверия D ---------------------------------------------
    M = len(recent)
    D = min(1.0, M / params.n_ref)  # базовый D; <1, если поездок < n_ref
    preliminary = D < 1.0

    category_by_dsi = _categorize(dsi, params)
    final_class = category_by_dsi

    # --- проверка устойчивости ---------------------------------------------
    if D == 1.0 and sigma_c > params.sigma_max:
        # устойчивость нарушена
        if previous_class is None:
            # первый расчёт → всё-таки задаём категорию, но D=0.5
            D = 0.5
            preliminary = True
        else:
            # категория уже существует → сохраняем её, D=0.8
            D = 0.8
            preliminary = True
            final_class = previous_class

    return DSIResult(
        dsi=round(dsi, 3),
        sigma=round(sigma_c, 3),
        trust=round(D, 2),
        profile_class=final_class,
        trips_used=M,
        preliminary=preliminary,
    )


def get_overall_category(trips: list[tuple]) -> str | None:
    trip_objects = [
        Trip(
            trip[0],
            TripClass.from_str(trip[1])
        )
        for trip in trips
    ]
    result = compute_driver_style(trip_objects, previous_class=None)
    if result:
        overall_category = result.profile_class.name.lower()
        return overall_category
    return None


# ───────────────────────── Демонстрация ─────────────────────

# if __name__ == "__main__":
    # from random import choice, randint

    # # пример: 3 случайные поездки (меньше 5 → D < 1)
    # now = datetime.datetime.now()
    # trips_demo = [
    #     Trip(now - timedelta(days=randint(1, 20)), choice(list(TripClass)))
    #     for _ in range(3)
    # ]
    # print(trips_demo)
    # print(list(TripClass))

    # res = compute_driver_style(trips_demo, previous_class=None)
    # if res is None:
    #     print("Нет данных для расчёта профиля.")
    # else:
    #     print(
    #         f"DSI = {res.dsi} | σ = {res.sigma} | D = {res.trust} | "
    #         f"class = {res.profile_class.name.lower()} | "
    #         f"preliminary = {res.preliminary} | trips = {res.trips_used}"
    #     )

    # trips = [
    #     (datetime.datetime(2025, 5, 20, 13, 15, 51, 900103, tzinfo=datetime.timezone.utc), 'aggressive'),
    #     (datetime.datetime(2025, 5, 20, 13, 15, 51, 900103, tzinfo=datetime.timezone.utc), 'aggressive'),
    #     (datetime.datetime(2025, 5, 20, 13, 15, 51, 900103, tzinfo=datetime.timezone.utc), 'aggressive')
    # ]

    # trips_demo = prepare_data(trips)
    # res = compute_driver_style(trips_demo, previous_class=None)
    # print(res.profile_class.name.lower())
