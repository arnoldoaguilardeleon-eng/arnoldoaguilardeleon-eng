#!/usr/bin/env python3
"""
Fetches the Lichess "puzzle of the day" and renders it as an SVG chessboard
(with the setup move highlighted and the first solving move drawn as an arrow),
so it can be embedded in a GitHub README and refreshed daily via GitHub Actions.
"""

import json
import sys
import urllib.request

import chess
import chess.pgn
import chess.svg
import io

LICHESS_DAILY_URL = "https://lichess.org/api/puzzle/daily"

LIGHT_SQUARE = "#f0d9b5"
DARK_SQUARE = "#b58863"
LAST_MOVE_COLOR = "#cdd26a"
ARROW_COLOR = "#15781B"


def fetch_daily_puzzle():
    req = urllib.request.Request(
        LICHESS_DAILY_URL, headers={"User-Agent": "github-readme-puzzle-bot"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def load_from_file(path):
    with open(path) as f:
        return json.load(f)


def build_board(data):
    pgn_moves = data["game"]["pgn"].split()
    initial_ply = data["puzzle"]["initialPly"]
    solution = data["puzzle"]["solution"]

    board = chess.Board()
    for i, san in enumerate(pgn_moves):
        if i >= initial_ply:
            break
        board.push_san(san)

    # The first solution move is the "setup" move already played for you;
    # the move after that is the one the solver actually has to find.
    setup_move = chess.Move.from_uci(solution[0])
    board.push(setup_move)

    puzzle_move = None
    if len(solution) > 1:
        puzzle_move = chess.Move.from_uci(solution[1])

    return board, setup_move, puzzle_move


def render_svg(board, setup_move, puzzle_move, orientation, path):
    arrows = []
    if puzzle_move:
        arrows.append(
            chess.svg.Arrow(puzzle_move.from_square, puzzle_move.to_square, color=ARROW_COLOR)
        )

    svg_data = chess.svg.board(
        board=board,
        lastmove=setup_move,
        arrows=arrows,
        orientation=orientation,
        size=360,
        coordinates=True,
    )
    with open(path, "w") as f:
        f.write(svg_data)


def write_info_snippet(data, board, path):
    puzzle = data["puzzle"]
    game = data["game"]
    turn = "Blancas" if board.turn == chess.WHITE else "Negras"
    themes = ", ".join(puzzle.get("themes", []))
    link = f"https://lichess.org/training/{puzzle['id']}"

    content = f"""<!-- AUTO-GENERATED: do not edit by hand, updated daily by chess-puzzle.yml -->
**Puzzle del día** · Rating {puzzle['rating']} · Turno: {turn}
Temas: {themes}
🔗 [Resolver en Lichess]({link})
"""
    with open(path, "w") as f:
        f.write(content)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        data = load_from_file(sys.argv[2])
    else:
        try:
            data = fetch_daily_puzzle()
        except Exception as e:
            print(f"Failed to fetch daily puzzle: {e}", file=sys.stderr)
            sys.exit(1)

    board, setup_move, puzzle_move = build_board(data)
    orientation = board.turn  # show the board from the side to move

    render_svg(board, setup_move, puzzle_move, orientation, "daily-puzzle.svg")
    write_info_snippet(data, board, "daily-puzzle-info.md")
    print("Puzzle generated:", data["puzzle"]["id"])


if __name__ == "__main__":
    main()
