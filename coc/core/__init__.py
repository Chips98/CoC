"""CoC core modules."""
from .bdp_tree import (
    BDP_NODE_TYPE, BDP_EDGES, ALL_NODES, BDP_PRIMITIVES,
    ROOT_CANDIDATES, LEAF_NODES, TERMINAL_NODES,
    legal_children, is_leaf, is_answer_node, validate_chain,
    all_paths, node_display_name,
)
from .engine import CoCEngine
from .mcts_search import SearchConfig, SearchState, search_cognition_chain, format_search_log
from .node_executor import NodeExecutor, NodeOutput
from .node_value import NodeStats
from .router import RouteResult, route_scene
from .theory_prior import scene_prior, build_theory_prior
from .memory_prior import build_memory_prior
from .reward import compute_pseudo_reward, compute_final_reward
from .answer_generator import AnswerGenerator

__all__ = [
    "BDP_NODE_TYPE", "BDP_EDGES", "ALL_NODES", "BDP_PRIMITIVES",
    "ROOT_CANDIDATES", "LEAF_NODES", "TERMINAL_NODES",
    "legal_children", "is_leaf", "is_answer_node", "validate_chain",
    "all_paths", "node_display_name",
    "CoCEngine",
    "SearchConfig", "SearchState", "search_cognition_chain", "format_search_log",
    "NodeExecutor", "NodeOutput",
    "NodeStats",
    "RouteResult", "route_scene",
    "scene_prior", "build_theory_prior",
    "build_memory_prior",
    "compute_pseudo_reward", "compute_final_reward",
    "AnswerGenerator",
]
