from database import Order
import config


def get_station_load():
    loads = {}
    for pc_id in config.COMPUTERS:
        count = Order.query.filter_by(
            computer_id=pc_id, status='new'
        ).count()
        loads[pc_id] = count
    return loads


def get_least_busy_station():
    loads = get_station_load()
    if not loads:
        return list(config.COMPUTERS.keys())[0]
    return min(loads, key=loads.get)


def get_overloaded_stations(threshold=5):
    loads = get_station_load()
    return [pc for pc, count in loads.items() if count >= threshold]


def suggest_redirect(current_pc_id):
    if current_pc_id not in config.COMPUTERS:
        return None
    current_load = get_station_load().get(current_pc_id, 0)
    if current_load < 5:
        return None
    least = get_least_busy_station()
    if least != current_pc_id:
        return least
    return None
