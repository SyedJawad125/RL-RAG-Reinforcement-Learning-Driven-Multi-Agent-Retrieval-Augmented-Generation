"""
RL Decision Agent
-----------------
Sits between the Planner and the execution agents.
Learns an adaptive policy: when to retrieve more, re-rank, answer, or
ask for clarification — using tabular Q-learning with experience replay.

Flow inside the coordinator:
    PlannerAgent
        ↓
    RLDecisionAgent  ← selects action every step
        ↓
    [RAGAgent | SearchAgent | Re-ranker | AnswerAgent]
        ↓   (loop until ANSWER_NOW or max steps)
    AnswerAgent (final synthesis)

Reward shaping:
    +1.0  high-confidence final answer
    +0.5  answer accompanied by citations
    +0.3  retrieval that actually improved confidence
    -0.5  unnecessary retrieval (confidence didn't improve)
    -1.0  low-confidence answer (hallucination risk)
    -0.05 per-step cost (encourages efficiency)
    +0.3  deferred user positive feedback
    -0.3  deferred user negative feedback
"""

import logging
from typing import Any, Dict, Optional, Tuple

from .base_agent import BaseAgent, AgentResult, AgentState
from services.agents.rl_memory import ACTIONS, ACTION_IDX, RLExperience, RLMemoryManager

logger = logging.getLogger(__name__)


class RLDecisionAgent(BaseAgent):
    """
    Reinforcement Learning Decision Agent.

    Selects one of four actions at each decision step:
        RETRIEVE_MORE      – run RAGAgent again (or with different top_k)
        RE_RANK            – re-score existing chunks and promote best ones
        ANSWER_NOW         – hand context to AnswerAgent immediately
        ASK_CLARIFICATION  – (async-safe fallback → ANSWER_NOW for now)

    The Q-table is updated after every action using:
        • Immediate proxy rewards (confidence delta, citation presence)
        • Deferred user-feedback rewards (applied via apply_user_feedback())
        • Experience replay (every 10 pushes to the buffer)
    """

    # Reward constants
    R_HIGH_CONF     = +1.00
    R_CITATION      = +0.50
    R_USEFUL_RETR   = +0.30
    R_USELESS_RETR  = -0.50
    R_LOW_CONF      = -1.00
    R_STEP_COST     = -0.05
    R_USER_POS      = +0.30
    R_USER_NEG      = -0.30

    MAX_STEPS = 5   # hard cap — prevents infinite loops

    def __init__(self, llm_service=None) -> None:
        super().__init__(
            name        = "RLDecisionAgent",
            description = "Q-learning based decision: retrieve / re-rank / answer",
            llm_service = llm_service,
        )
        self.memory = RLMemoryManager()

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN EXECUTE
    # ─────────────────────────────────────────────────────────────────────────

    async def execute(self, state: AgentState) -> AgentResult:
        """
        Select the next action for the current agent state.

        Returns an AgentResult whose ``output`` field is the action name
        string (e.g. "RETRIEVE_MORE"), so the coordinator knows what to do.
        """
        try:
            rl_state   = self._build_state(state)
            action_idx = self.memory.q_table.select_action(rl_state, training=True)
            action_name = ACTIONS[action_idx]

            # Enforce max-step guard
            step_count = state.metadata.get("rl_step_count", 0)
            if step_count >= self.MAX_STEPS - 1:
                action_idx  = ACTION_IDX["ANSWER_NOW"]
                action_name = "ANSWER_NOW"
                self.add_observation(state, f"Max steps ({self.MAX_STEPS}) reached — forcing ANSWER_NOW")

            # Persist decision into state for reward calculation
            state.metadata["rl_state"]       = rl_state
            state.metadata["rl_action"]      = action_idx
            state.metadata["rl_action_name"] = action_name
            state.metadata["rl_step_count"]  = step_count + 1

            # Log Q-values (transparency / debugging)
            q_vals   = self.memory.q_table.q_values(rl_state)
            q_table  = {ACTIONS[i]: round(v, 3) for i, v in enumerate(q_vals)}

            self.add_thought(state, f"RL state: {rl_state}")
            self.add_action(state, f"Selected action: {action_name}", "rl_qtable")
            self.add_observation(state, f"Q-values → {q_table}")

            return self.create_result(
                success    = True,
                output     = action_name,
                state      = state,
                confidence = 0.9,
            )

        except Exception as exc:
            logger.error(f"[RLDecisionAgent] execute error: {exc}", exc_info=True)
            state.metadata["rl_action_name"] = "ANSWER_NOW"
            return self.create_result(
                success    = True,
                output     = "ANSWER_NOW",
                state      = state,
                confidence = 0.5,
            )

    # ─────────────────────────────────────────────────────────────────────────
    #  REWARD + EXPERIENCE STORAGE
    # ─────────────────────────────────────────────────────────────────────────

    def record_experience(
        self,
        state:          AgentState,
        next_state_data: Dict[str, Any],
        done:           bool,
        query_id:       str = "",
    ) -> float:
        """
        Compute reward, push experience to replay buffer, update Q-table.
        Called by the coordinator after every action completes.

        Args:
            state:           Agent state BEFORE the action
            next_state_data: Dict with keys: confidence, retrieved_count,
                             complexity, has_internet, has_citations
            done:            True on the final (ANSWER_NOW) step
            query_id:        DB UUID of the query (for deferred feedback)

        Returns:
            The computed reward (float).
        """
        prev_state = state.metadata.get("rl_state")
        action_idx = state.metadata.get("rl_action", ACTION_IDX["ANSWER_NOW"])

        if prev_state is None:
            return 0.0

        reward         = self._compute_reward(state, next_state_data, done)
        next_rl_state  = self._state_from_dict(next_state_data)

        experience = RLExperience(
            state      = prev_state,
            action     = action_idx,
            reward     = reward,
            next_state = next_rl_state,
            done       = done,
            query_id   = str(query_id),
        )
        self.memory.replay_buf.push(experience)

        # Immediate Q-update
        self.memory.q_table.update(
            prev_state, action_idx, reward, next_rl_state, done
        )

        # Periodic replay (every 10 new experiences)
        if len(self.memory.replay_buf) % 10 == 0:
            self.memory.replay_train(batch_size=32)

        # Persist Q-table to disk on terminal step
        if done:
            self.memory.save()

        # Save reward back to state for logging / DB
        state.metadata["rl_reward"] = reward

        # Persist experience to DB
        self._save_experience_to_db(
            query_id       = query_id,
            rl_state       = list(prev_state),
            action_idx     = action_idx,
            reward         = reward,
            next_rl_state  = list(next_rl_state),
            done           = done,
        )

        logger.info(
            f"[RLDecisionAgent] reward={reward:+.3f} | "
            f"action={ACTIONS[action_idx]} | done={done} | ε={self.memory.q_table.epsilon:.4f}"
        )
        return reward

    def apply_user_feedback(
        self,
        query_id: str,
        feedback: str,   # "positive" | "negative"
    ) -> None:
        """
        Apply deferred user feedback as an additional reward signal.
        Called from views.py when the user rates an answer (thumbs up/down).
        """
        from apps.rag.models import RLExperienceRecord

        delta = self.R_USER_POS if feedback == "positive" else self.R_USER_NEG

        try:
            records = RLExperienceRecord.objects.filter(query_id=query_id)
            for rec in records:
                s = tuple(rec.rl_state)
                a = rec.action_idx
                self.memory.q_table.update(s, a, delta, s, done=True)
                rec.user_feedback = feedback
                rec.reward       += delta
                rec.save()

            self.memory.save()
            logger.info(
                f"[RLDecisionAgent] User feedback '{feedback}' applied "
                f"to query {query_id} | Δ={delta:+.2f}"
            )
        except Exception as exc:
            logger.error(f"[RLDecisionAgent] apply_user_feedback error: {exc}")

    # ─────────────────────────────────────────────────────────────────────────
    #  RE-RANKING HELPER
    # ─────────────────────────────────────────────────────────────────────────

    async def re_rank_chunks(
        self,
        query:  str,
        chunks: list,
        state:  AgentState,
    ) -> list:
        """
        LLM-based re-ranking of retrieved chunks.
        Called when the RL agent selects RE_RANK.

        Scores each chunk 1-10 for relevance, returns sorted list.
        Falls back to original order on any failure.
        """
        if not chunks or not self.llm_service:
            return chunks

        self.add_action(state, "Re-ranking chunks via LLM", "re_ranker")

        try:
            scored = []
            for chunk in chunks[:8]:   # Cap at 8 to stay within token budget
                snippet = chunk.get("content", "")[:300]
                prompt = (
                    f"Rate how relevant this text is for answering the question.\n"
                    f"Question: {query}\n"
                    f"Text: {snippet}\n"
                    f"Reply with ONLY a number from 1 (irrelevant) to 10 (highly relevant)."
                )
                resp = await self.call_llm(prompt, temperature=0.0, max_tokens=5)
                try:
                    score = float(resp.strip().split()[0])
                except (ValueError, IndexError):
                    score = 5.0
                scored.append({**chunk, "rl_rerank_score": score})

            ranked = sorted(scored, key=lambda c: c.get("rl_rerank_score", 0), reverse=True)
            self.add_observation(state, f"Re-ranked {len(ranked)} chunks")
            return ranked

        except Exception as exc:
            logger.warning(f"[RLDecisionAgent] re_rank_chunks fallback: {exc}")
            return chunks

    # ─────────────────────────────────────────────────────────────────────────
    #  STATE BUILDING
    # ─────────────────────────────────────────────────────────────────────────

    def _build_state(self, state: AgentState) -> Tuple:
        """Build discretised RL state from live AgentState."""
        meta    = state.metadata
        context = state.context

        # Confidence bucket
        confidence  = meta.get("relevance_check", {}).get("score", 0.5)
        conf_bucket = 0 if confidence < 0.4 else (1 if confidence < 0.7 else 2)

        # Retrieval bucket
        n_chunks    = len(meta.get("retrieved_chunks", []))
        retr_bucket = 0 if n_chunks == 0 else (1 if n_chunks <= 3 else (2 if n_chunks <= 7 else 3))

        # Complexity bucket
        complexity  = meta.get("query_complexity", "medium")
        comp_bucket = {"simple": 0, "medium": 1, "complex": 2}.get(str(complexity), 1)

        # Internet flag
        has_internet = int(
            "search_results" in meta or "tavily_answer" in meta
        )

        return (conf_bucket, retr_bucket, comp_bucket, has_internet)

    def _state_from_dict(self, d: Dict[str, Any]) -> Tuple:
        """Build RL state from a plain dict (used for next_state)."""
        conf = d.get("confidence", 0.5)
        c    = 0 if conf < 0.4 else (1 if conf < 0.7 else 2)

        n    = d.get("retrieved_count", 0)
        r    = 0 if n == 0 else (1 if n <= 3 else (2 if n <= 7 else 3))

        comp = {"simple": 0, "medium": 1, "complex": 2}.get(
            d.get("complexity", "medium"), 1
        )
        i = int(d.get("has_internet", False))
        return (c, r, comp, i)

    # ─────────────────────────────────────────────────────────────────────────
    #  REWARD COMPUTATION
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_reward(
        self,
        state:     AgentState,
        next_data: Dict[str, Any],
        done:      bool,
    ) -> float:
        """
        Compute scalar reward.

        Terminal step  → confidence-based reward ± citation bonus
        Non-terminal   → efficiency-based shaping (was the action useful?)
        Always         → small step cost to encourage brevity
        """
        action_name = ACTIONS[state.metadata.get("rl_action", ACTION_IDX["ANSWER_NOW"])]
        reward      = self.R_STEP_COST   # always pay step cost

        if done:
            conf = next_data.get("confidence", 0.5)
            reward += self.R_HIGH_CONF if conf >= 0.75 else (
                       0.30           if conf >= 0.50 else
                       self.R_LOW_CONF)
            if next_data.get("has_citations", False):
                reward += self.R_CITATION

        else:
            if action_name == "RETRIEVE_MORE":
                prev_conf = (
                    state.metadata.get("relevance_check", {}).get("score", 0.5)
                )
                new_conf  = next_data.get("confidence", prev_conf)
                reward   += (
                    self.R_USEFUL_RETR if new_conf > prev_conf + 0.10
                    else self.R_USELESS_RETR
                )

            elif action_name == "RE_RANK":
                reward += 0.20 if next_data.get("confidence", 0.5) > 0.6 else -0.10

        return round(reward, 4)

    # ─────────────────────────────────────────────────────────────────────────
    #  DB PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _save_experience_to_db(
        query_id:      str,
        rl_state:      list,
        action_idx:    int,
        reward:        float,
        next_rl_state: list,
        done:          bool,
    ) -> None:
        """Persist experience for later feedback and analysis."""
        try:
            from apps.rag.models import RLExperienceRecord
            RLExperienceRecord.objects.create(
                query_id      = query_id,
                rl_state      = rl_state,
                action_idx    = action_idx,
                action_name   = ACTIONS[action_idx],
                reward        = reward,
                next_rl_state = next_rl_state,
                done          = done,
            )
        except Exception as exc:
            logger.warning(f"[RLDecisionAgent] DB persist skipped: {exc}")

    # ─────────────────────────────────────────────────────────────────────────
    #  STATS
    # ─────────────────────────────────────────────────────────────────────────

    def get_rl_stats(self) -> Dict[str, Any]:
        qt = self.memory.q_table
        sample_states = {
            k: {ACTIONS[i]: round(v, 3) for i, v in enumerate(vals)}
            for k, vals in list(qt.table.items())[:5]
        }
        return {
            "epsilon":         round(qt.epsilon, 4),
            "total_updates":   qt.total_updates,
            "states_learned":  len(qt.table),
            "replay_buf_size": len(self.memory.replay_buf),
            "actions":         list(ACTIONS.values()),
            "q_table_sample":  sample_states,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name":         self.name,
            "description":  self.description,
            "capabilities": [
                "Epsilon-greedy Q-learning",
                "Experience replay (capacity=10k)",
                "Deferred user-feedback integration",
                "LLM-based chunk re-ranking",
                "Adaptive retrieval strategy",
            ],
            "actions":       list(ACTIONS.values()),
            "output_format": "action_name_string",
        }