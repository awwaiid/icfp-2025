#!/usr/bin/env python3
import subprocess
import json

def run_explore():
    result = subprocess.run(['./bin/explore', '1', '2', '3'], capture_output=True, text=True)
    if result.returncode != 0:
        print('Error running ./bin/explore:', result.stderr)
        exit(1)
    return result.stdout.strip()

def parse_output(output):
    # Find the first line that looks like JSON and parse it
    for line in output.splitlines():
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):  # crude JSON detection
            try:
                data = json.loads(line)
                results = data.get('results', [])
                query_count = data.get('queryCount', 0)
                return results, query_count
            except json.JSONDecodeError:
                continue
    print('No valid JSON found in output!')
    return [], 0

def build_grid(coords):
    if not coords:
        return []
    max_x = max(x for x, y in coords)
    max_y = max(y for x, y in coords)
    grid = [['.' for _ in range(max_y + 1)] for _ in range(max_x + 1)]
    for x, y in coords:
        grid[x][y] = '#'
    return grid

def print_ascii_grid(grid):
    print('ASCII Visualization:')
    for row in grid:
        print(' '.join(row))

def main():
    output = run_explore()
    results, query_count = parse_output(output)
    grid = build_grid(results)
    print_ascii_grid(grid)
    print(f'\nQuery count: {query_count}')

if __name__ == '__main__':
    main()
