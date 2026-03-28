"""
RL Memory Manager
-----------------
Q-Table (tabular Q-learning) + Experience Replay Buffer.
Persists the learned policy to disk across Django restarts.

State space (4 discrete dims):
    conf_bucket       → 0/1/2  (low / medium / high confidence)
    retrieval_bucket  → 0/1/2/3 (none / few / moderate / many chunks)
    complexity_bucket → 0/1/2  (simple / medium / complex query)
    has_internet      → 0/1    (internet results available?)

Action space:
    0 → RETRIEVE_MORE
    1 → RE_RANK
    2 → ANSWER_NOW
    3 → ASK_CLARIFICATION
"""

import json
import os
import random
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  ACTION MAP
# ─────────────────────────────────────────────────────────────────────────────

ACTIONS: Dict[int, str] = {
    0: "RETRIEVE_MORE",
    1: "RE_RANK",
    2: "ANSWER_NOW",
    3: "ASK_CLARIFICATION",
}

ACTION_IDX: Dict[str, int] = {v: k for k, v in ACTIONS.items()}


# ─────────────────────────────────────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RLExperience:
    """Single (s, a, r, s', done) tuple for replay buffer."""
    state:      Tuple
    action:     int
    reward:     float
    next_state: Tuple
    done:       bool
    query_id:   str = ""


# ─────────────────────────────────────────────────────────────────────────────
#  Q-TABLE
# ─────────────────────────────────────────────────────────────────────────────

class QTable:
    """
    Tabular Q-learning.

    Q(s, a) ← Q(s, a) + α [r + γ max Q(s', ·) − Q(s, a)]

    State keys are stored as stringified tuples so the table can be
    serialised to / deserialised from plain JSON.
    """

    def __init__(
        self,
        n_actions:     int   = 4,
        learning_rate: float = 0.1,
        discount:      float = 0.9,
        epsilon:       float = 0.3,
        epsilon_min:   float = 0.05,
        epsilon_decay: float = 0.995,
    ):
        self.n_actions     = n_actions
        self.lr            = learning_rate
        self.gamma         = discount
        self.epsilon       = epsilon
        self.epsilon_min   = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.table:        Dict[str, List[float]] = {}
        self.total_updates: int = 0

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _key(state: Tuple) -> str:
        return str(state)

    def _init_state(self, state: Tuple) -> List[float]:
        """
        Optimistic initialisation:
          RETRIEVE_MORE=0.5, RE_RANK=0.3, ANSWER_NOW=0.7, ASK_CLARIF=0.2
        Biases the agent toward answering first, trying retrieval second.
        """
        return [0.5, 0.3, 0.7, 0.2]

    # ── public API ────────────────────────────────────────────────────────────

    def q_values(self, state: Tuple) -> List[float]:
        key = self._key(state)
        if key not in self.table:
            self.table[key] = self._init_state(state)
        return self.table[key]

    def best_action(self, state: Tuple) -> int:
        return int(np.argmax(self.q_values(state)))

    def select_action(self, state: Tuple, training: bool = True) -> int:
        """Epsilon-greedy action selection."""
        if training and random.random() < self.epsilon:
            return random.randrange(self.n_actions)
        return self.best_action(state)

    def update(
        self,
        state:      Tuple,
        action:     int,
        reward:     float,
        next_state: Tuple,
        done:       bool,
    ) -> None:
        """Standard Q-learning update."""
        current_q = self.q_values(state)[action]

        if done:
            target = reward
        else:
            target = reward + self.gamma * max(self.q_values(next_state))

        q = self.q_values(state)
        q[action] = current_q + self.lr * (target - current_q)
        self.table[self._key(state)] = q

        # Decay exploration
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_updates += 1

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        payload = {
            "table":         self.table,
            "epsilon":       self.epsilon,
            "total_updates": self.total_updates,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"[QTable] Saved {len(self.table)} states → {path}")

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            logger.info("[QTable] No checkpoint found — fresh start")
            return
        with open(path) as f:
            data = json.load(f)
        self.table         = data.get("table", {})
        self.epsilon       = data.get("epsilon", self.epsilon)
        self.total_updates = data.get("total_updates", 0)
        logger.info(
            f"[QTable] Loaded {len(self.table)} states | "
            f"ε={self.epsilon:.4f} | updates={self.total_updates}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  EXPERIENCE REPLAY BUFFER
# ─────────────────────────────────────────────────────────────────────────────

class ExperienceReplayBuffer:
    """Fixed-capacity circular buffer — O(1) push, O(k) random sample."""

    def __init__(self, capacity: int = 10_000):
        self._buf: deque = deque(maxlen=capacity)

    def push(self, exp: RLExperience) -> None:
        self._buf.append(exp)

    def sample(self, k: int) -> List[RLExperience]:
        return random.sample(self._buf, min(k, len(self._buf)))

    def __len__(self) -> int:
        return len(self._buf)


# ─────────────────────────────────────────────────────────────────────────────
#  SINGLETON MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class RLMemoryManager:
    """
    Process-level singleton that owns the Q-table and replay buffer.
    Thread-safe enough for Django's typical single-threaded async workers.
    """

    _instance: Optional["RLMemoryManager"] = None

    def __new__(cls) -> "RLMemoryManager":
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._ready = False
            cls._instance = obj
        return cls._instance

    def __init__(self) -> None:
        if self._ready:
            return

        from django.conf import settings

        self.q_table_path = str(
            getattr(
                settings,
                "RL_QTABLE_PATH",
                Path(getattr(settings, "BASE_DIR", ".")) / "rl_qtable.json",
            )
        )

        self.q_table = QTable(
            n_actions     = 4,
            learning_rate = float(getattr(settings, "RL_LEARNING_RATE", 0.1)),
            discount      = float(getattr(settings, "RL_DISCOUNT",       0.9)),
            epsilon       = float(getattr(settings, "RL_EPSILON",        0.3)),
            epsilon_min   = float(getattr(settings, "RL_EPSILON_MIN",   0.05)),
            epsilon_decay = float(getattr(settings, "RL_EPSILON_DECAY", 0.995)),
        )
        self.q_table.load(self.q_table_path)

        replay_cap       = int(getattr(settings, "RL_REPLAY_CAPACITY", 10_000))
        self.replay_buf  = ExperienceReplayBuffer(capacity=replay_cap)
        self._ready      = True
        logger.info("[RLMemoryManager] Initialized")

    # ── helpers ──────────────────────────────────────────────────────────────

    def save(self) -> None:
        self.q_table.save(self.q_table_path)

    def replay_train(self, batch_size: int = 32) -> None:
        """Sample from buffer and run Q-learning updates."""
        if len(self.replay_buf) < batch_size:
            return
        batch = self.replay_buf.sample(batch_size)
        for exp in batch:
            self.q_table.update(
                exp.state, exp.action, exp.reward, exp.next_state, exp.done
            )
        self.save()
        logger.debug(f"[RLMemoryManager] Replay-trained on {len(batch)} experiences")