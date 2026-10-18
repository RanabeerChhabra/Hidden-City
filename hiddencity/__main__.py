"""Command line entry point.

    python -m hiddencity budget                      # searches left, free to run
    python -m hiddencity scan --dates 2026-11-18     # spend searches, fill the cache
    python -m hiddencity report                      # analyse everything in the cache
"""

import argparse
import time

from hiddencity import client, config, detect, parse, storage


def cmd_budget(args):
    api_key = client.get_api_key()
    account = client.account_status(api_key)
    print("Plan:", account.get("plan_name"))
    print("Searches left this month:", account.get("total_searches_left"))
    print("Used this month:", account.get("this_month_usage"))
    print(f"Used in the last hour (our log): {client.searches_in_last_hour()}/{config.HOURLY_LIMIT}")


def fetch_with_wait(destination, date, api_key, wait):
    """Fetch one search. With wait=True, sleep through the hourly limit instead of stopping."""
    while True:
        try:
            return client.fetch_flights(config.ORIGIN, destination, date, api_key)
        except client.HourlyLimitReached:
            if not wait:
                raise
            print("  Hourly limit reached, waiting 10 minutes...")
            time.sleep(600)


def cmd_scan(args):
    api_key = client.get_api_key()
    destinations = args.destinations or list(config.DESTINATIONS)

    todo = []
    for date in args.dates:
        for destination in destinations:
            if not client.is_cached(config.ORIGIN, destination, date):
                todo.append((destination, date))

    total = len(destinations) * len(args.dates)
    print(f"{total} searches planned, {total - len(todo)} already cached, {len(todo)} to fetch.")
    if args.max_searches is not None:
        todo = todo[: args.max_searches]

    left = client.account_status(api_key).get("total_searches_left")
    if left is not None and len(todo) > left:
        print(f"Only {left} searches left this month; fetching the first {left}.")
        todo = todo[:left]
    if not todo:
        print("Nothing to fetch.")
        return

    fetched = 0
    failed = []
    for destination, date in todo:
        label = f"{config.ORIGIN}->{destination} {date}"
        try:
            data = fetch_with_wait(destination, date, api_key, args.wait)
        except client.HourlyLimitReached as e:
            print(f"Stopping: {e} Run again later (or add --wait) to continue.")
            break
        except client.SearchError as e:
            print(f"  FAILED {label}: {e}")
            failed.append(label)
            continue
        fetched += 1
        count = len(data.get("best_flights", [])) + len(data.get("other_flights", []))
        print(f"  {label}: {count} itineraries")
        time.sleep(config.PAUSE_BETWEEN_SEARCHES)

    print(f"Done. Fetched {fetched}, failed {len(failed)}.")
    if failed:
        print("Failed searches are not cached, so running scan again will retry them.")


def load_all_rows():
    rows = []
    for destination, date in client.cached_searches(config.ORIGIN):
        data = client.load_cached(config.ORIGIN, destination, date)
        rows.extend(parse.parse_itineraries(data, destination, date))
    return rows


def cmd_report(args):
    rows = load_all_rows()
    if not rows:
        print("The cache is empty. Run `python -m hiddencity scan` first.")
        return
    opportunities = detect.find_hidden_city(rows)
    summary = detect.summarise(rows, opportunities)
    storage.save_results(rows, opportunities)

    searches = len(client.cached_searches(config.ORIGIN))
    print(f"Searches analysed: {searches}   Itineraries: {len(rows)}")
    print(f"Hub routes with a known direct price: {summary['routes_checked']}")
    print(
        f"Routes with a hidden-city saving: {summary['routes_with_saving']} "
        f"({summary['pct_routes_with_saving']}%)"
    )
    if opportunities:
        print(f"Average best saving per route: Rs {summary['avg_best_saving']}")
        print(f"Biggest saving: Rs {summary['max_saving']}")
        print()
        print("Top savings:")
        for opp in opportunities[: args.top]:
            print(
                f"  {opp['date']}  {opp['origin']}->{opp['hub']} (ticket to {opp['final_destination']})"
                f"  {opp['airline']} {opp['first_flight']}"
                f"  Rs {opp['hidden_city_price']} vs Rs {opp['cheapest_direct_price']} direct"
                f"  save Rs {opp['saving']} ({opp['saving_pct']}%)"
            )
    print()
    print(f"Saved to {storage.DB_PATH.relative_to(config.ROOT)} and data/*.csv")


def main():
    parser = argparse.ArgumentParser(prog="hiddencity", description="Hidden-city fare analysis.")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("budget", help="show searches left (free)")

    scan = commands.add_parser("scan", help="search flights and cache the answers")
    scan.add_argument("--dates", nargs="+", required=True, help="YYYY-MM-DD, one or more")
    scan.add_argument("--destinations", nargs="+", help="airport codes (default: all in config)")
    scan.add_argument("--max-searches", type=int, help="stop after this many paid searches")
    scan.add_argument("--wait", action="store_true", help="wait out the hourly limit instead of stopping")

    report = commands.add_parser("report", help="find hidden-city fares in the cache")
    report.add_argument("--top", type=int, default=15, help="how many savings to list")

    args = parser.parse_args()
    if args.command == "budget":
        cmd_budget(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()
