"""
Quantum AI Engine v4.4 — Enhanced Multi-Algorithm Optimization
Algorithms: Simulated Annealing, Genetic Algorithm, Tabu Search, Ant Colony + Ensemble
"""
import numpy as np, random, math, json, hashlib, time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
from collections import defaultdict, deque
import copy

@dataclass
class Task:
    id: str
    priority: float = 1.0
    duration: float = 10.0
    resource_req: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    location: Tuple[float, float] = (0.0, 0.0)
    deadline: Optional[float] = None
    skill_req: str = "general"

@dataclass
class Resource:
    id: str
    capacity: float = 100.0
    location: Tuple[float, float] = (0.0, 0.0)
    skills: List[str] = field(default_factory=lambda: ["general"])
    speed: float = 1.0
    fatigue: float = 0.0
    current_load: float = 0.0

class QuantumAIEngine:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.task_history = deque(maxlen=10000)
        self.congestion_model = defaultdict(lambda: {"count": 0, "avg_time": 0.0})
        self.ensemble_weights = {"sa": 0.25, "ga": 0.25, "tabu": 0.25, "aco": 0.25}
        self.version = "4.4.0"

    # ── Simulated Annealing ──────────────────────────────────
    def simulated_annealing(self, tasks: List[Task], resources: List[Resource],
                            initial_temp: float = 1000, cooling_rate: float = 0.995,
                            iterations: int = 2000) -> Tuple[Dict, float]:
        def random_solution():
            sol = {}
            for t in tasks:
                eligible = [r for r in resources if t.skill_req in r.skills and r.current_load + t.duration <= r.capacity]
                sol[t.id] = self.rng.choice(eligible).id if eligible else self.rng.choice(resources).id
            return sol

        def neighbor(sol):
            s = dict(sol)
            tid = self.rng.choice(list(s.keys()))
            eligible = [r for r in resources if any(t.id == tid and t.skill_req in r.skills for t in tasks)]
            s[tid] = self.rng.choice(eligible).id if eligible else self.rng.choice(resources).id
            return s

        def cost(sol):
            return self._evaluate(sol, tasks, resources)

        current = random_solution()
        current_cost = cost(current)
        best, best_cost = dict(current), current_cost
        temp = initial_temp

        for _ in range(iterations):
            nxt = neighbor(current)
            nxt_cost = cost(nxt)
            delta = nxt_cost - current_cost
            if delta < 0 or self.rng.random() < math.exp(-delta / temp):
                current, current_cost = nxt, nxt_cost
                if current_cost < best_cost:
                    best, best_cost = dict(current), current_cost
            temp *= cooling_rate
        return best, best_cost

    # ── Genetic Algorithm ────────────────────────────────────
    def genetic_algorithm(self, tasks: List[Task], resources: List[Resource],
                          pop_size: int = 50, generations: int = 100,
                          mutation_rate: float = 0.1, crossover_rate: float = 0.8) -> Tuple[Dict, float]:
        def encode():
            return {t.id: self.rng.choice([r.id for r in resources]) for t in tasks}

        def mutate(chromo):
            c = dict(chromo)
            if self.rng.random() < mutation_rate:
                tid = self.rng.choice(list(c.keys()))
                c[tid] = self.rng.choice([r.id for r in resources])
            return c

        def crossover(p1, p2):
            if self.rng.random() > crossover_rate:
                return dict(p1)
            child = {}
            for k in p1:
                child[k] = p1[k] if self.rng.random() < 0.5 else p2[k]
            return child

        population = [encode() for _ in range(pop_size)]
        for _ in range(generations):
            scored = [(self._evaluate(p, tasks, resources), p) for p in population]
            scored.sort(key=lambda x: x[0])
            elite = [s[1] for s in scored[:pop_size // 4]]
            new_pop = elite[:]
            while len(new_pop) < pop_size:
                p1, p2 = self.rng.choices(elite, k=2)
                child = mutate(crossover(p1, p2))
                new_pop.append(child)
            population = new_pop
        best = min(population, key=lambda p: self._evaluate(p, tasks, resources))
        return best, self._evaluate(best, tasks, resources)

    # ── Tabu Search ──────────────────────────────────────────
    def tabu_search(self, tasks: List[Task], resources: List[Resource],
                    tabu_tenure: int = 20, iterations: int = 500) -> Tuple[Dict, float]:
        def random_sol():
            return {t.id: self.rng.choice([r.id for r in resources]) for t in tasks}

        def neighbors(sol):
            nbrs = []
            for _ in range(min(20, len(tasks) * 2)):
                s = dict(sol)
                tid = self.rng.choice(list(s.keys()))
                s[tid] = self.rng.choice([r.id for r in resources])
                nbrs.append(s)
            return nbrs

        current = random_sol()
        best, best_cost = dict(current), self._evaluate(current, tasks, resources)
        tabu_list = deque(maxlen=tabu_tenure)

        for _ in range(iterations):
            nbrs = neighbors(current)
            valid = [n for n in nbrs if str(n) not in tabu_list]
            if not valid:
                valid = nbrs
            nxt = min(valid, key=lambda n: self._evaluate(n, tasks, resources))
            nxt_cost = self._evaluate(nxt, tasks, resources)
            tabu_list.append(str(current))
            current = nxt
            if nxt_cost < best_cost:
                best, best_cost = dict(nxt), nxt_cost
        return best, best_cost

    # ── Ant Colony Optimization ──────────────────────────────
    def ant_colony(self, tasks: List[Task], resources: List[Resource],
                   n_ants: int = 30, iterations: int = 80,
                   alpha: float = 1.0, beta: float = 2.0, evap: float = 0.5) -> Tuple[Dict, float]:
        pheromone = defaultdict(lambda: defaultdict(lambda: 1.0))
        best_sol, best_cost = None, float('inf')

        for _ in range(iterations):
            for _ in range(n_ants):
                sol = {}
                for t in tasks:
                    eligible = [r for r in resources if t.skill_req in r.skills]
                    if not eligible:
                        eligible = resources
                    probs = []
                    for r in eligible:
                        tau = pheromone[t.id][r.id] ** alpha
                        eta = (1.0 / (1 + self._task_resource_cost(t, r))) ** beta
                        probs.append(tau * eta)
                    total = sum(probs)
                    probs = [p / total for p in probs]
                    chosen = self.np_rng.choice([r.id for r in eligible], p=probs)
                    sol[t.id] = chosen
                cost = self._evaluate(sol, tasks, resources)
                if cost < best_cost:
                    best_sol, best_cost = dict(sol), cost
                for t in tasks:
                    pheromone[t.id][sol[t.id]] += 1.0 / (1 + cost)
            for t in tasks:
                for r in resources:
                    pheromone[t.id][r.id] *= evap
        return best_sol, best_cost

    # ── Ensemble Optimizer ───────────────────────────────────
    def ensemble_optimize(self, tasks: List[Task], resources: List[Resource],
                          method_weights: Optional[Dict[str, float]] = None) -> Dict:
        weights = method_weights or self.ensemble_weights
        results = {}
        if weights.get("sa", 0) > 0:
            results["sa"] = self.simulated_annealing(tasks, resources)
        if weights.get("ga", 0) > 0:
            results["ga"] = self.genetic_algorithm(tasks, resources)
        if weights.get("tabu", 0) > 0:
            results["tabu"] = self.tabu_search(tasks, resources)
        if weights.get("aco", 0) > 0:
            results["aco"] = self.ant_colony(tasks, resources)

        # Weighted vote aggregation
        vote_counts = defaultdict(lambda: defaultdict(float))
        for method, (sol, cost) in results.items():
            w = weights.get(method, 0.25)
            for tid, rid in sol.items():
                vote_counts[tid][rid] += w * (1.0 / (1 + cost))

        final = {}
        for tid, votes in vote_counts.items():
            final[tid] = max(votes, key=votes.get)
        return final

    # ── Predictive Congestion ────────────────────────────────
    def predict_congestion(self, zone: str, time_window: float = 3600) -> Dict:
        data = self.congestion_model.get(zone, {"count": 0, "avg_time": 0.0})
        predicted = data["count"] * (1 + 0.1 * math.sin(time.time() / 3600))
        return {
            "zone": zone,
            "predicted_tasks": round(predicted, 1),
            "avg_processing_time": round(data["avg_time"], 2),
            "congestion_level": "high" if predicted > 50 else "medium" if predicted > 20 else "low",
            "recommendation": "Add resources" if predicted > 50 else "Monitor"
        }

    def record_task_completion(self, zone: str, processing_time: float):
        d = self.congestion_model[zone]
        d["count"] += 1
        d["avg_time"] = (d["avg_time"] * (d["count"] - 1) + processing_time) / d["count"]

    # ── Cost Functions ───────────────────────────────────────
    def _evaluate(self, assignment: Dict[str, str], tasks: List[Task], resources: List[Resource]) -> float:
        res_map = {r.id: r for r in resources}
        task_map = {t.id: t for t in tasks}
        total = 0.0
        load = defaultdict(float)

        for tid, rid in assignment.items():
            t = task_map[tid]
            r = res_map[rid]
            # Distance cost
            dist = math.dist(t.location, r.location)
            total += dist * 0.5
            # Duration cost
            total += t.duration * (1 + r.fatigue)
            # Skill mismatch
            if t.skill_req not in r.skills:
                total += 100
            # Load balancing
            load[rid] += t.duration
            # Deadline penalty
            if t.deadline and t.duration > t.deadline:
                total += 50

        # Load variance penalty
        loads = list(load.values())
        if loads:
            avg_load = sum(loads) / len(loads)
            variance = sum((l - avg_load) ** 2 for l in loads) / len(loads)
            total += variance * 2

        return total

    def _task_resource_cost(self, task: Task, resource: Resource) -> float:
        dist = math.dist(task.location, resource.location)
        skill_pen = 0 if task.skill_req in resource.skills else 50
        return dist + task.duration + skill_pen + resource.fatigue * 10

    def get_health(self) -> Dict:
        return {
            "version": self.version,
            "algorithms": ["simulated_annealing", "genetic_algorithm", "tabu_search", "ant_colony", "ensemble"],
            "task_history_size": len(self.task_history),
            "congestion_zones": list(self.congestion_model.keys()),
            "ensemble_weights": dict(self.ensemble_weights),
            "status": "healthy"
        }
