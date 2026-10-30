"""Observed purchase/undo and normal skill-level sequences, never optimal builds."""
import math

ITEM_EVENTS = {'ITEM_PURCHASED', 'ITEM_SOLD', 'ITEM_DESTROYED', 'ITEM_UNDO'}


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def loadout_histories(match, timeline):
    people = match['info']['participants']
    duration = match['info']['gameDuration'] * 1000
    result = {player['participantId']: {'status': 'unavailable', 'item_events': [],
        'purchases': [], 'skill_order': [], 'unresolved_undos': 0,
        'invalid_events': 0, 'complete_timeline': False} for player in people}
    if (not isinstance(timeline, dict) or not isinstance(timeline.get('metadata'), dict)
            or timeline['metadata'].get('matchId') != match['metadata']['matchId']
            or not isinstance(timeline.get('info'), dict)
            or not isinstance(timeline['info'].get('frames'), list)):
        return result
    events, frames_seen, complete = [], set(), False
    expected = {str(pid) for pid in result}
    for frame in timeline['info']['frames']:
        if not isinstance(frame, dict):
            continue
        stamp = frame.get('timestamp')
        if (type(stamp) in (int, float) and math.isfinite(stamp)
                and duration-120000 <= stamp <= duration+120000
                and isinstance(frame.get('participantFrames'), dict)
                and set(frame['participantFrames']) == expected):
            complete = True
        raw = frame.get('events')
        if not isinstance(raw, list):
            continue
        # Repeated frames are ignored; identical purchases inside one frame can be real.
        identity = repr((stamp, raw))
        if identity in frames_seen:
            continue
        frames_seen.add(identity)
        for event in raw:
            if not isinstance(event, dict) or event.get('type') not in ITEM_EVENTS | {'SKILL_LEVEL_UP'}:
                continue
            pid = event.get('participantId')
            if not integer(pid, 1, 10) or pid not in result:
                continue
            timestamp = event.get('timestamp')
            if not integer(timestamp, 0, math.ceil(duration)+5000):
                result[pid]['invalid_events'] += 1
                continue
            events.append(event)
    transactions = {pid: [] for pid in result}
    for event in sorted(events, key=lambda row: row['timestamp']):
        pid, kind = event['participantId'], event['type']
        row, stack = result[pid], transactions[pid]
        if kind == 'SKILL_LEVEL_UP':
            if event.get('levelUpType') != 'NORMAL':
                continue  # Evolutions are not ordinary Q/W/E/R skill-point choices.
            if not integer(event.get('skillSlot'), 1, 4):
                row['invalid_events'] += 1
                continue
            row['skill_order'].append({'timestamp_ms': event['timestamp'], 'slot': event['skillSlot'],
                                      'ability': 'QWER'[event['skillSlot']-1]})
            continue
        item = {'timestamp_ms': event['timestamp'], 'kind': kind, 'undone': False}
        if kind == 'ITEM_UNDO':
            before, after = event.get('beforeId'), event.get('afterId')
            item.update(before_id=before if integer(before, 0, 9999999) else None,
                        after_id=after if integer(after, 0, 9999999) else None, reverses=None)
            previous = row['item_events'][stack[-1]] if stack else None
            if (previous and ((previous['kind'] == 'ITEM_PURCHASED' and before == previous['item_id'] and after == 0)
                              or (previous['kind'] == 'ITEM_SOLD' and before == 0 and after == previous['item_id']))
                    and type(before) is int and type(after) is int):
                index = stack.pop()
                previous['undone'] = True
                item['reverses'] = index
            else:
                row['unresolved_undos'] += 1
        else:
            if not integer(event.get('itemId'), 1, 9999999):
                row['invalid_events'] += 1
                continue
            item['item_id'] = event['itemId']
            if kind in ('ITEM_PURCHASED', 'ITEM_SOLD'):
                stack.append(len(row['item_events']))
        row['item_events'].append(item)
    for row in result.values():
        row['purchases'] = [{'item_id': item['item_id'], 'timestamp_ms': item['timestamp_ms']}
                            for item in row['item_events'] if item['kind'] == 'ITEM_PURCHASED' and not item['undone']]
        row['complete_timeline'] = complete
        row['status'] = 'partial' if not complete or row['invalid_events'] or row['unresolved_undos'] else 'available'
        row['purchase_aggregate_eligible'] = complete and not row['invalid_events'] and not row['unresolved_undos'] and bool(row['purchases'])
        row['skill_aggregate_eligible'] = complete and not row['invalid_events'] and bool(row['skill_order'])
    return result
