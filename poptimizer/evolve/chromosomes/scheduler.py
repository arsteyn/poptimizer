"""Гены и хромосома ответственные за политику обучения."""
from poptimizer.evolve.chromosomes import chromosome

MAX_LR = chromosome.GeneParams(
    path=("scheduler", "max_lr"),
    default_range=(0.001, 0.01),
    lower_bound=0.0,
    upper_bound=None,
    phenotype_function=float,
)
EPOCHS = chromosome.GeneParams(
    path=("scheduler", "epochs"),
    default_range=(1.1, 1.2),
    lower_bound=1.0,
    upper_bound=None,
    phenotype_function=int,
)
PCT_START = chromosome.GeneParams(
    path=("scheduler", "pct_start"),
    default_range=(0.299, 0.301),
    lower_bound=0.0,
    upper_bound=1.0,
    phenotype_function=float,
)
ANNEAL_STRATEGY = chromosome.GeneParams(
    path=("scheduler", "anneal_strategy"),
    default_range=(0.1, 0.9),
    lower_bound=0.0,
    upper_bound=1.99,
    phenotype_function=lambda x: {0: "cos", 1: "linear"}[int(x)],
)
BASE_MOMENTUM = chromosome.GeneParams(
    path=("scheduler", "base_momentum"),
    default_range=(0.849, 0.851),
    lower_bound=0.0,
    upper_bound=1.0,
    phenotype_function=float,
)
MAX_MOMENTUM = chromosome.GeneParams(
    path=("scheduler", "max_momentum"),
    default_range=(0.949, 0.951),
    lower_bound=0.0,
    upper_bound=1.0,
    phenotype_function=float,
)
DIV_FACTOR = chromosome.GeneParams(
    path=("scheduler", "div_factor"),
    default_range=(24.9, 25.1),
    lower_bound=1.0,
    upper_bound=None,
    phenotype_function=float,
)
FINAL_DIV_FACTOR = chromosome.GeneParams(
    path=("scheduler", "final_div_factor"),
    default_range=(0.999e4, 1.01e4),
    lower_bound=1.0,
    upper_bound=None,
    phenotype_function=float,
)


class Scheduler(chromosome.Chromosome):
    """Хромосома ответственная за параметры One cycle learning rate policy."""

    _GENES = (
        MAX_LR,  # Максимальная скорость обучения
        EPOCHS,  # Количество эпох обучения
        PCT_START,  # Доля шагов разогрева
        ANNEAL_STRATEGY,  # Стратегия снижения скорости обучения
        BASE_MOMENTUM,  # Базовый моментум
        MAX_MOMENTUM,  # Максимальный моментум
        DIV_FACTOR,  # Понижающий коэффициент скорости обучения для периода разогрева
        FINAL_DIV_FACTOR,  # Понижающий коэффициент для скорости обучения в конце цикла понижения
    )
