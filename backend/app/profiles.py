"""Descriptive profiles from the displayed matches, separate from model inputs."""
from statistics import mean


ROLES = ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY')
MIN_COMPARISON_GAMES = 3


def _metrics(matches: list[dict]) -> dict:
    games = len(matches)
    wins = sum(match['win'] for match in matches)
    return {
        'games': games, 'wins': wins,
        'win_rate': wins / games if games else None,
        'kda': round(sum(m['kills'] + m['assists'] for m in matches)
                     / max(1, sum(m['deaths'] for m in matches)), 2) if games else None,
        'cs_per_min': round(mean(m['cs_per_min'] for m in matches), 2) if games else None,
        'kill_participation': round(mean(m['kill_participation'] for m in matches), 4) if games else None,
        'vision_per_min': round(mean(m['vision_score'] / m['duration_minutes'] for m in matches), 2) if games else None,
    }


def player_profile(matches: list[dict]) -> dict:
    """Count each match once; an unseen role has no observed win rate."""
    matches = list({match['id']: match for match in reversed(matches)}.values())
    roles = [{'role': role, **_metrics([m for m in matches if m['role'] == role])}
             for role in ROLES]
    champions = [{'champion': champion, **_metrics([m for m in matches if m['champion'] == champion])}
                 for champion in sorted({m['champion'] for m in matches})]
    champions.sort(key=lambda group: (-group['games'], group['champion']))
    largest = max(role['games'] for role in roles)
    most_played = [role['role'] for role in roles if largest and role['games'] == largest]
    main_role = most_played[0] if len(most_played) == 1 else None
    known = [m for m in matches if m['role'] in ROLES]
    main_stats = _metrics([m for m in known if m['role'] == main_role]) if main_role else None
    off_stats = _metrics([m for m in known if m['role'] != main_role]) if main_role else None
    return {
        'games': len(matches), 'roles': roles, 'champions': champions,
        'unknown_role_games': len(matches) - len(known),
        'main_role': main_role, 'main_role_tied': len(most_played) > 1,
        'main_role_stats': main_stats, 'off_role_stats': off_stats,
        'main_off_role_win_rate_gap': (round(main_stats['win_rate'] - off_stats['win_rate'], 4)
                                       if main_stats and off_stats and off_stats['games'] else None),
        'notice': ('Only the loaded, eligible matches are counted. Most-played role describes this '
                   'sample, not your preferred role or autofill status. Win rates are descriptive; '
                   'small groups and mixed patches/queues do not establish skill or improvement.'),
    }


def personal_comparison(match: dict, matches: list[dict]) -> dict:
    """Compare with other displayed games, never reuse the selected match."""
    others = list({m['id']: m for m in reversed(matches) if m['id'] != match['id']}.values())
    role_games = [m for m in others if m['role'] == match['role']] if match['role'] in ROLES else []
    champion_games = [m for m in role_games if m['champion'] == match['champion']]
    basis, baseline = ('same_champion_role', champion_games) if len(champion_games) >= MIN_COMPARISON_GAMES else ('same_role', role_games)
    if len(baseline) < MIN_COMPARISON_GAMES:
        return {
            'basis': 'none', 'games': len(role_games), 'averages': None, 'deltas': None,
            'notice': (f'At least {MIN_COMPARISON_GAMES} other loaded games in the same known role '
                       'are needed for a personal comparison. No benchmark is invented.'),
        }
    averages = {
        'cs_per_min': round(mean(m['cs_per_min'] for m in baseline), 2),
        'kill_participation': round(mean(m['kill_participation'] for m in baseline), 4),
        'vision_per_min': round(mean(m['vision_score'] / m['duration_minutes'] for m in baseline), 2),
        'deaths_per_game': round(mean(m['deaths'] for m in baseline), 2),
    }
    current = {'cs_per_min': match['cs_per_min'], 'kill_participation': match['kill_participation'],
               'vision_per_min': match['vision_score'] / match['duration_minutes'],
               'deaths_per_game': match['deaths']}
    return {
        'basis': basis, 'games': len(baseline), 'averages': averages,
        'deltas': {key: round(current[key] - value, 4) for key, value in averages.items()},
        'notice': ('Selected match excluded. Other displayed matches may be earlier or later. '
                   'These final-statistic comparisons are for post-match review only, not model '
                   'inputs or evidence that a change caused the result. Three games is a display '
                   'minimum, not statistical validation.'),
    }


def comparison_insight(match: dict, comparison: dict) -> dict | None:
    if comparison['averages'] is None:
        return None
    reference = 'same champion and role' if comparison['basis'] == 'same_champion_role' else 'same role'
    averages = comparison['averages']
    return {
        'title': 'Compare with your own games',
        'detail': (f"In {comparison['games']} other loaded games in the {reference}, you averaged "
                   f"{averages['cs_per_min']:.1f} CS/min, {averages['kill_participation']:.0%} kill "
                   f"participation and {averages['vision_per_min']:.2f} vision/min. This match: "
                   f"{match['cs_per_min']:.1f}, {match['kill_participation']:.0%} and "
                   f"{match['vision_score'] / match['duration_minutes']:.2f}. Review differences "
                   'in matchup, duration and game state before setting a goal; this small '
                   'sample is not a skill ranking or a causal explanation.'),
        'tone': 'neutral',
    }
