"""Create reproducible fictional raw fixtures, never real-player evidence."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import random


def generate_records(count: int = 300, seed: int = 20261026) -> list[dict]:
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    records = []
    start = 1_760_000_000_000
    for index in range(count):
        advantage = rng.gauss(0, 1)
        match_id = f"SYNTHETIC_{seed}_{index:05d}"
        pframes = {}
        participants = []
        for pid in range(1, 11):
            team = 100 if pid <= 5 else 200
            side = 1 if team == 100 else -1
            participants.append({"participantId": pid, "teamId": team,
                                 "puuid": f"fictional-{index}-{pid}", "championName": "DemoChampion"})
            pframes[str(pid)] = {"participantId": pid,
                                "totalGold": max(1500, int(3300 + side * advantage * 220 + rng.gauss(0, 220))),
                                "xp": max(1500, int(4300 + side * advantage * 190 + rng.gauss(0, 350))),
                                "minionsKilled": max(10, int(60 + side * advantage * 6 + rng.gauss(0, 10))),
                                "jungleMinionsKilled": rng.randrange(0, 21)}
        events = []
        for _ in range(rng.randrange(5, 21)):
            blue = rng.random() < 1 / (1 + math.exp(-advantage * 0.55))
            killer = rng.randrange(1, 6) if blue else rng.randrange(6, 11)
            events.append({"type": "CHAMPION_KILL", "timestamp": rng.randrange(90_000, 600_001),
                           "killerId": killer, "victimId": 6 if blue else 1})
        for _ in range(rng.randrange(0, 3)):
            blue = rng.random() < 1 / (1 + math.exp(-advantage * 0.5))
            events.append({"type": "BUILDING_KILL", "timestamp": rng.randrange(400_000, 600_001),
                           "buildingType": "TOWER_BUILDING", "teamId": 200 if blue else 100})
        if rng.random() < 0.8:
            blue = rng.random() < 1 / (1 + math.exp(-advantage * 0.4))
            events.append({"type": "ELITE_MONSTER_KILL", "timestamp": rng.randrange(310_000, 600_001),
                           "monsterType": "DRAGON", "killerId": 2 if blue else 7,
                           "killerTeamId": 100 if blue else 200})
        # A stochastic fictional label, not a simulator of League of Legends.
        blue_win = rng.random() < 1 / (1 + math.exp(-advantage * 0.85))
        records.append({"source": "synthetic", "match": {
            "metadata": {"matchId": match_id}, "info": {
                "mapId": 11, "queueId": 420 if index % 4 else 440,
                "gameDuration": 1800 + rng.randrange(-300, 600),
                "gameStartTimestamp": start + index * 3_600_000,
                "gameVersion": "fictional-demo-v1", "participants": participants,
                "teams": [{"teamId": 100, "win": blue_win}, {"teamId": 200, "win": not blue_win}]}},
            "timeline": {"metadata": {"matchId": match_id}, "info": {"frameInterval": 60_000,
                "frames": [{"timestamp": 600_000, "participantFrames": pframes, "events": events},
                           {"timestamp": 1_200_000, "participantFrames": pframes,
                            "events": [{"type": "CHAMPION_KILL", "timestamp": 1_100_000,
                                        "killerId": 1, "victimId": 6}]}]}}})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "synthetic_training.jsonl")
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20261026)
    args = parser.parse_args()
    records = generate_records(args.count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as target:
        for record in records:
            target.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(f"Wrote {len(records)} SYNTHETIC fictional matches to {args.output}; no real-world accuracy claim.")


if __name__ == "__main__":
    main()
