import random
import time
import chess

# Nilai dasar material bidak catur
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Piece-Square Tables (PST) untuk mode Sulit (Perspektif Putih; dibalik untuk Hitam)
# Mendorong penguasaan tengah, perkembangan perwira, dan keamanan raja
PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

PST_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

PST_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

PST_ROOK = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

PST_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

PST_KING_MIDGAME = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]


def evaluate_board(board: chess.Board) -> int:
    """
    Evaluasi posisi papan secara statis dari sudut pandang Putih (positif = Putih unggul).
    Memperhitungkan nilai material dan tabel posisi bidak (PST).
    """
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        val = PIECE_VALUES.get(piece.piece_type, 0)
        pst_val = 0

        # Ambil nilai PST
        sq_idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
        pt = piece.piece_type
        if pt == chess.PAWN:
            pst_val = PST_PAWN[sq_idx]
        elif pt == chess.KNIGHT:
            pst_val = PST_KNIGHT[sq_idx]
        elif pt == chess.BISHOP:
            pst_val = PST_BISHOP[sq_idx]
        elif pt == chess.ROOK:
            pst_val = PST_ROOK[sq_idx]
        elif pt == chess.QUEEN:
            pst_val = PST_QUEEN[sq_idx]
        elif pt == chess.KING:
            pst_val = PST_KING_MIDGAME[sq_idx]

        total_piece_score = val + pst_val
        if piece.color == chess.WHITE:
            score += total_piece_score
        else:
            score -= total_piece_score

    return score


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
    """
    Algoritma Minimax dengan Alpha-Beta Pruning dan pengurutan langkah untuk optimasi kecepatan.
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    # Move ordering: Utamakan langkah makan (capture) & promosi terlebih dahulu
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: (board.is_capture(m), m.promotion is not None), reverse=True)

    if is_maximizing:
        max_eval = -999999
        for move in moves:
            board.push(move)
            ev = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, ev)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 999999
        for move in moves:
            board.push(move)
            ev = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, ev)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval


class MimiChessEngine:
    """
    Engine AI Catur untuk Mimi si Kucing Virtual.
    Mendukung 3 Mode Kesulitan:
    - 'Mudah' (Easy): Santai, acak 50-60%, sesekali blunder imut.
    - 'Normal' (Normal): Minimax depth 2, memperhatikan material & kontrol posisi.
    - 'Sulit' (Hard): Minimax Alpha-Beta depth 3-4 + PST, pertahanan & serangan taktis tajam.
    """
    def __init__(self, pet_name: str = "Mimi"):
        self.pet_name = pet_name

    def get_greeting(self, difficulty: str) -> str:
        diff = difficulty.capitalize()
        if diff == "Mudah":
            greetings = [
                f"Meow! Ayo main santai, Tuan! Mimi mainnya pelan-pelan ya! 🐾",
                f"Purrr~ Mode Mudah diaktifkan! Mimi siap bersenang-senang! 🐱",
                f"Nyaa! Mimi cuma anak kucing biasa di mode ini, jangan skakmat cepat-cepat ya! 🐾"
            ]
        elif diff == "Sulit":
            greetings = [
                f"Meoww! Mode SULIT diaktifkan! Kucing Master Mimi siap menunjukkan strategi tingkat tinggi! 😼♟️",
                f"Purrr~ Tuan menantang Mimi mode master? Pasang kuda-kuda, strategi cakar tajam dimulai! 🐾⚔️",
                f"Nyaa! Mimi sudah membaca ribuan taktik catur, tunjukkan langkah terbaikmu, Tuan! 😼"
            ]
        else: # Normal
            greetings = [
                f"Meow! Mode Normal siap! Ayo kita adu taktik yang seru dan berimbang, Tuan! 🐾",
                f"Purrr~ Mimi siap melangkah dengan hati-hati. Semoga yang terbaik yang menang! 🐱♟️",
                f"Nyaa! Pion siap maju! Mari nikmati permainannya, Tuan! 🐾"
            ]
        return random.choice(greetings)

    def select_move(self, board: chess.Board, difficulty: str = "Normal") -> tuple:
        """
        Memilih langkah terbaik berdasarkan tingkat kesulitan.
        Mengembalikan tuple: (chess.Move, str_komentar_mimi)
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, "Meow... tidak ada langkah legal lagi! Permainan selesai."

        diff = difficulty.capitalize()
        chosen_move = None
        is_ai_white = (board.turn == chess.WHITE)

        # ----------------------------------------
        # 1. MODE MUDAH (EASY)
        # ----------------------------------------
        if diff == "Mudah":
            # 60% acak, 40% memilih langkah makan atau pengembangan perwira
            captures = [m for m in legal_moves if board.is_capture(m)]
            if captures and random.random() < 0.45:
                chosen_move = random.choice(captures)
            else:
                chosen_move = random.choice(legal_moves)

        # ----------------------------------------
        # 2. MODE NORMAL (MEDIUM)
        # ----------------------------------------
        elif diff == "Normal":
            # Minimax depth 2 dengan sedikit variasi acak jika skor mirip
            scored_moves = []
            for move in legal_moves:
                board.push(move)
                score = minimax(board, depth=1, alpha=-999999, beta=999999, is_maximizing=not is_ai_white)
                board.pop()
                scored_moves.append((score, move))

            # Urutkan berdasarkan perspektif AI
            if is_ai_white:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
            else:
                scored_moves.sort(key=lambda x: x[0], reverse=False)

            # Pilih dari top 2 jika skor sangat dekat agar pergerakan tidak monoton
            top_score = scored_moves[0][0]
            close_moves = [m for s, m in scored_moves[:3] if abs(s - top_score) < 30]
            chosen_move = random.choice(close_moves) if close_moves else scored_moves[0][1]

        # ----------------------------------------
        # 3. MODE SULIT (HARD)
        # ----------------------------------------
        else: # Sulit
            # Minimax depth 3 dengan Alpha-Beta Pruning dan PST lengkap
            best_score = -999999 if is_ai_white else 999999
            best_move = legal_moves[0]

            # Urutkan langkah untuk pemangkasan alpha-beta optimal
            sorted_moves = sorted(legal_moves, key=lambda m: (board.is_capture(m), m.promotion is not None), reverse=True)

            for move in sorted_moves:
                board.push(move)
                score = minimax(board, depth=2, alpha=-999999, beta=999999, is_maximizing=not is_ai_white)
                board.pop()

                if is_ai_white:
                    if score > best_score:
                        best_score = score
                        best_move = move
                else:
                    if score < best_score:
                        best_score = score
                        best_move = move

            chosen_move = best_move

        if chosen_move is None:
            chosen_move = random.choice(legal_moves)

        # Hasilkan celetukan kontekstual Mimi setelah memilih langkah
        comment = self._generate_move_comment(board, chosen_move, diff)
        return chosen_move, comment

    def _generate_move_comment(self, board: chess.Board, move: chess.Move, difficulty: str) -> str:
        """Menghasilkan dialog lucu Mimi berdasarkan sifat langkah yang diambil."""
        is_capture = board.is_capture(move)
        san = board.san(move)
        board.push(move)
        is_check = board.is_check()
        is_checkmate = board.is_checkmate()
        board.pop()

        piece = board.piece_at(move.from_square)
        piece_name = "Bidak"
        if piece:
            names = {
                chess.PAWN: "Pion", chess.KNIGHT: "Kuda", chess.BISHOP: "Gajah",
                chess.ROOK: "Benteng", chess.QUEEN: "Menteri", chess.KING: "Raja"
            }
            piece_name = names.get(piece.piece_type, "Bidak")

        if is_checkmate:
            return f"🏆 *SKAKMAT!* Meoww! Mimi berhasil skakmat dengan {piece_name} ({san})! Pertandingan yang seru sekali Tuan! 🐾✨"

        if is_check:
            check_comments = [
                f"😼 *Skak!* Awas rajanya, Tuan! {piece_name} Mimi mengincar ke {san}! 🐾",
                f"Meow! Skak! Hati-hati langkah penyelamatannya ya Tuan! ⚠️",
                f"Purrr~ Cakar Mimi mendekat ke Raja! Skak ({san})! 🐱"
            ]
            return random.choice(check_comments)

        if is_capture:
            cap_comments = [
                f"🐾 *Hap!* Mimi amankan bidak Tuan di {chess.square_name(move.to_square)}! Nyam~ 🐟",
                f"Purrrr~ Bidak lezat tertangkap oleh cakar {piece_name} Mimi! 😼",
                f"Meow! Bidak Tuan Mimi singkirkan ya! ({san}) 🐾"
            ]
            return random.choice(cap_comments)

        if move.promotion:
            return f"✨ *Promosi!* Pion Mimi bertransformasi menjadi perwira hebat ({san})! Meow! 👑🐾"

        normal_comments = [
            f"Nyaa~ Mimi gerakkan {piece_name} ke {chess.square_name(move.to_square)} ({san})! 🐾",
            f"Purrr~ Giliran Tuan melangkah! Mimi tunggu aksimu! 🐱",
            f"Meow! Langkah taktis Mimi: {san}! Silakan Tuan! 🐾",
            f"*{self.pet_name} menatap papan dengan mata pixel penasaran* Giliranmu Tuan! 🐾"
        ]
        return random.choice(normal_comments)

    def get_game_over_comment(self, board: chess.Board, player_is_white: bool) -> str:
        """Komentar saat permainan selesai (Menang, Kalah, Remis)."""
        if board.is_checkmate():
            # Pihak yang giliran melangkah adalah yang terkena skakmat
            winner_is_white = not board.turn
            player_won = (winner_is_white == player_is_white)
            if player_won:
                return "👑 *Luar Biasa, Tuan!* Skakmat sempurna! Mimi kalah telak, Tuan sangat hebat bermain catur! 🥺🐾 Saluuut! 🏆"
            else:
                return "🏆 *Meowww! Skakmat!* Cakar taktis Mimi berhasil memenangkan pertandingan ini! Terima kasih untuk permainannya, Tuan! 🐾✨"
        elif board.is_stalemate():
            return "🤝 *Remis (Stalemate)!* Raja tidak bisa melangkah lagi namun tidak skak. Permainan berakhir imbang yang damai! 🐾"
        elif board.is_insufficient_material():
            return "🤝 *Remis!* Bidak di papan tidak cukup lagi untuk skakmat. Hasil imbang yang terhormat! 🐾"
        else:
            return "🤝 *Permainan Berakhir Imbang!* Keseimbangan strategi yang sangat mengagumkan, Tuan! 🐾"
