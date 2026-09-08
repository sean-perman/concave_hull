from dataclasses import dataclass


VALID_KNN_BACKENDS = ("scipy",)
VALID_K_GROWTH_STRATEGIES = ("linear", "exponential", "binary_search")
VALID_FAILURE_STRATEGIES = ("restart", "checkpoint")
VALID_CHECKPOINT_STRATEGIES = ("none", "extreme", "convex_hull")
VALID_CHECKPOINT_K_SCOPES = ("per_region", "global")
VALID_INTERSECTION_STRATEGIES = ("naive", "bucketed")
VALID_VALIDATION_MODES = ("off", "report", "enforce")


@dataclass(frozen=True)
class ConcaveHullConfig:
    initial_k: int = 3
    knn_backend: str = "scipy"
    k_growth_strategy: str = "linear"
    k_growth_rate: float = 2.0  # only used by "exponential"
    failure_strategy: str = "restart"
    checkpoint_strategy: str = "none"  # only used by failure_strategy="checkpoint"
    # How k rises after a checkpoint failure: "per_region" bumps only the failing
    # region's k (independent, more adaptive, but each region re-climbs from initial_k);
    # "global" bumps a single shared k for all regions (like restart's global k, but
    # keeps the trimmed prefix) — a more direct comparison to the restart baseline.
    checkpoint_k_scope: str = "per_region"
    intersection_strategy: str = "naive"
    intersection_bucket_size: float = 0.0  # 0 or negative = auto from data extent
    validate_final_hull: str = "off"  # "off" | "report" | "enforce"

    def __post_init__(self):
        if self.knn_backend not in VALID_KNN_BACKENDS:
            raise ValueError(
                f"knn_backend must be one of {VALID_KNN_BACKENDS}, got {self.knn_backend!r}"
            )
        if self.k_growth_strategy not in VALID_K_GROWTH_STRATEGIES:
            raise ValueError(
                f"k_growth_strategy must be one of {VALID_K_GROWTH_STRATEGIES}, "
                f"got {self.k_growth_strategy!r}"
            )
        if self.failure_strategy not in VALID_FAILURE_STRATEGIES:
            raise ValueError(
                f"failure_strategy must be one of {VALID_FAILURE_STRATEGIES}, "
                f"got {self.failure_strategy!r}"
            )
        if self.checkpoint_strategy not in VALID_CHECKPOINT_STRATEGIES:
            raise ValueError(
                f"checkpoint_strategy must be one of {VALID_CHECKPOINT_STRATEGIES}, "
                f"got {self.checkpoint_strategy!r}"
            )
        if self.checkpoint_k_scope not in VALID_CHECKPOINT_K_SCOPES:
            raise ValueError(
                f"checkpoint_k_scope must be one of {VALID_CHECKPOINT_K_SCOPES}, "
                f"got {self.checkpoint_k_scope!r}"
            )
        if self.intersection_strategy not in VALID_INTERSECTION_STRATEGIES:
            raise ValueError(
                f"intersection_strategy must be one of {VALID_INTERSECTION_STRATEGIES}, "
                f"got {self.intersection_strategy!r}"
            )
        if self.validate_final_hull not in VALID_VALIDATION_MODES:
            raise ValueError(
                f"validate_final_hull must be one of {VALID_VALIDATION_MODES}, "
                f"got {self.validate_final_hull!r}"
            )
        if self.initial_k < 3:
            raise ValueError(f"initial_k must be >= 3, got {self.initial_k}")
        if self.k_growth_rate <= 1.0:
            raise ValueError(f"k_growth_rate must be > 1.0, got {self.k_growth_rate}")
        # Cross-field constraints.
        if self.failure_strategy == "checkpoint":
            if self.checkpoint_strategy == "none":
                raise ValueError(
                    "failure_strategy='checkpoint' requires checkpoint_strategy "
                    "in ('extreme', 'convex_hull')"
                )
            if self.k_growth_strategy == "binary_search":
                raise ValueError(
                    "k_growth_strategy='binary_search' is incompatible with "
                    "failure_strategy='checkpoint' (bisection needs end-to-end feedback)"
                )
