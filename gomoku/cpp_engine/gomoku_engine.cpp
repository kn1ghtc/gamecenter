/**
 * Gomoku AI Engine - C++ Implementation
 */

#include "gomoku_engine.hpp"
#include <chrono>
#include <random>
#include <cmath>

namespace gomoku {

// Direction vectors for line checking
static const int dx[] = {0, 1, 1, 1};  // horizontal, vertical, diagonal1, diagonal2
static const int dy[] = {1, 0, 1, -1};

// Zobrist Hasher Implementation
ZobristHasher::ZobristHasher() {
    // Initialize random number generator
    std::mt19937_64 rng(12345);  // Fixed seed for reproducibility
    std::uniform_int_distribution<uint64_t> dist;
    
    // Generate random 64-bit numbers for each position and player
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            table[row][col][0] = dist(rng);  // BLACK
            table[row][col][1] = dist(rng);  // WHITE
        }
    }
}

uint64_t ZobristHasher::compute_hash(const Board& board) const {
    uint64_t hash = 0;
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int8_t player = board.get(row, col);
            if (player != EMPTY) {
                int player_idx = (player == BLACK) ? 0 : 1;
                hash ^= table[row][col][player_idx];
            }
        }
    }
    return hash;
}

// Board Implementation
bool Board::check_win(int row, int col, Player player) const {
    if (get(row, col) != player) return false;
    
    // Check 4 directions
    for (int dir = 0; dir < 4; ++dir) {
        int count = 1;  // Count the placed stone
        
        // Check positive direction
        for (int step = 1; step < 5; ++step) {
            int r = row + dx[dir] * step;
            int c = col + dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == player) {
                count++;
            } else {
                break;
            }
        }
        
        // Check negative direction
        for (int step = 1; step < 5; ++step) {
            int r = row - dx[dir] * step;
            int c = col - dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == player) {
                count++;
            } else {
                break;
            }
        }
        
        if (count >= 5) return true;
    }
    
    return false;
}

int Board::quick_evaluate(int row, int col, Player player) const {
    if (!is_empty(row, col)) return -INF;
    
    int score = 0;
    
    // Distance to center bonus
    int center = BOARD_SIZE / 2;
    int dist = std::abs(row - center) + std::abs(col - center);
    score += (15 - dist) * 10;
    
    // Check connectivity in 4 directions
    for (int dir = 0; dir < 4; ++dir) {
        // Count my stones
        int my_count = 0;
        for (int step = 1; step <= 4; ++step) {
            int r = row + dx[dir] * step;
            int c = col + dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == player) my_count++;
            else break;
        }
        for (int step = 1; step <= 4; ++step) {
            int r = row - dx[dir] * step;
            int c = col - dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == player) my_count++;
            else break;
        }
        score += my_count * my_count * 100;
        
        // Count opponent stones (defense)
        Player opponent = (player == BLACK) ? WHITE : BLACK;
        int opp_count = 0;
        for (int step = 1; step <= 4; ++step) {
            int r = row + dx[dir] * step;
            int c = col + dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == opponent) opp_count++;
            else break;
        }
        for (int step = 1; step <= 4; ++step) {
            int r = row - dx[dir] * step;
            int c = col - dy[dir] * step;
            if (in_bounds(r, c) && get(r, c) == opponent) opp_count++;
            else break;
        }
        score += opp_count * opp_count * 80;
    }
    
    return score;
}

// AI Engine Implementation
AIEngine::AIEngine() : nodes_searched(0), search_time(0.0) {
    tt.clear();
    killer_moves.clear();
}

Move AIEngine::find_best_move(Player player, int max_depth, double time_limit) {
    auto start = std::chrono::high_resolution_clock::now();
    
    nodes_searched = 0;
    Move best_move;
    uint64_t hash_key = zobrist.compute_hash(board);
    
    // Iterative deepening with aspiration window
    int prev_score = 0;
    for (int depth = 1; depth <= max_depth; ++depth) {
        int alpha, beta;
        
        if (depth == 1) {
            alpha = -INF;
            beta = INF;
        } else {
            // Aspiration window
            int window = 50;
            alpha = prev_score - window;
            beta = prev_score + window;
        }
        
        // Search with narrow window
        int score = minimax(player, depth, alpha, beta, true, hash_key);
        
        // Re-search if outside window
        if (score <= alpha || score >= beta) {
            score = minimax(player, depth, -INF, INF, true, hash_key);
        }
        
        prev_score = score;
        
        // Get best move from TT
        TTEntry* entry = tt.probe(hash_key);
        if (entry && entry->best_row >= 0) {
            best_move.row = entry->best_row;
            best_move.col = entry->best_col;
            best_move.score = entry->score;
        }
        
        // Check time limit
        auto now = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = now - start;
        if (elapsed.count() > time_limit * 0.8) break;
        
        // Early termination for winning move
        if (score > WIN_SCORE - 100) break;
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    search_time = elapsed.count();
    
    return best_move;
}

std::vector<Move> AIEngine::generate_moves(Player player) {
    std::vector<Move> moves;
    moves.reserve(50);
    
    if (board.move_count == 0) {
        // First move: center
        int center = BOARD_SIZE / 2;
        moves.emplace_back(center, center, 0);
        return moves;
    }
    
    // Get empty neighbors (distance 2)
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            if (!board.is_empty(row, col)) continue;
            
            // Check if has neighbor within distance 2
            bool has_neighbor = false;
            for (int dr = -2; dr <= 2 && !has_neighbor; ++dr) {
                for (int dc = -2; dc <= 2 && !has_neighbor; ++dc) {
                    if (dr == 0 && dc == 0) continue;
                    int r = row + dr;
                    int c = col + dc;
                    if (board.in_bounds(r, c) && !board.is_empty(r, c)) {
                        has_neighbor = true;
                    }
                }
            }
            
            if (has_neighbor) {
                int score = board.quick_evaluate(row, col, player);
                moves.emplace_back(row, col, score);
            }
        }
    }
    
    // Sort by score (descending)
    std::sort(moves.begin(), moves.end(), [](const Move& a, const Move& b) {
        return a.score > b.score;
    });
    
    // Return top 15 moves
    if (moves.size() > 15) {
        moves.resize(15);
    }
    
    return moves;
}

int AIEngine::evaluate(Player player) const {
    // Simple evaluation: count patterns
    int score = 0;
    Player opponent = (player == BLACK) ? WHITE : BLACK;
    
    // Check all lines
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            for (int dir = 0; dir < 4; ++dir) {
                // Extract line of 5
                std::array<int8_t, 5> line;
                bool valid = true;
                for (int i = 0; i < 5; ++i) {
                    int r = row + dx[dir] * i;
                    int c = col + dy[dir] * i;
                    if (board.in_bounds(r, c)) {
                        line[i] = board.get(r, c);
                    } else {
                        valid = false;
                        break;
                    }
                }
                
                if (valid) {
                    score += evaluate_line(line, player);
                    score -= evaluate_line(line, opponent);
                }
            }
        }
    }
    
    return score;
}

int AIEngine::evaluate_line(const std::array<int8_t, 5>& line, Player player) const {
    int count = 0;
    int empty = 0;
    
    for (int8_t cell : line) {
        if (cell == player) count++;
        else if (cell == EMPTY) empty++;
    }
    
    // If opponent stones present, no score
    if (empty + count < 5) return 0;
    
    // Score based on count
    if (count == 5) return WIN_SCORE;
    if (count == 4 && empty == 1) return 10000;
    if (count == 3 && empty == 2) return 1000;
    if (count == 2 && empty == 3) return 100;
    if (count == 1 && empty == 4) return 10;
    
    return 0;
}

int AIEngine::minimax(Player player, int depth, int alpha, int beta, 
                      bool is_maximizing, uint64_t hash_key) {
    nodes_searched++;
    
    // TT probe
    TTEntry* entry = tt.probe(hash_key);
    if (entry && entry->depth >= depth) {
        if (entry->flag == 0) return entry->score;  // Exact
        if (entry->flag == 1 && entry->score > alpha) alpha = entry->score;  // Lower bound
        if (entry->flag == 2 && entry->score < beta) beta = entry->score;   // Upper bound
        if (alpha >= beta) return entry->score;
    }
    
    // Terminal node
    if (depth == 0) {
        return evaluate(player);
    }
    
    // Generate moves
    Player current_player = is_maximizing ? player : (player == BLACK ? WHITE : BLACK);
    std::vector<Move> moves = generate_moves(current_player);
    
    if (moves.empty()) {
        return 0;
    }
    
    // Add killer moves to front
    const auto& killers = killer_moves.get(depth);
    for (const Move& killer : killers) {
        if (killer.row >= 0 && board.is_empty(killer.row, killer.col)) {
            // Move killer to front
            auto it = std::find_if(moves.begin(), moves.end(), 
                [&killer](const Move& m) {
                    return m.row == killer.row && m.col == killer.col;
                });
            if (it != moves.end()) {
                std::rotate(moves.begin(), it, it + 1);
            }
        }
    }
    
    int best_score = is_maximizing ? -INF : INF;
    int8_t best_row = -1, best_col = -1;
    
    for (const Move& move : moves) {
        // Make move
        board.place(move.row, move.col, current_player);
        uint64_t new_hash = zobrist.update_hash(hash_key, move.row, move.col, current_player);
        
        // Check immediate win
        if (board.check_win(move.row, move.col, current_player)) {
            board.undo(move.row, move.col);
            if (is_maximizing) {
                return WIN_SCORE - (MAX_DEPTH - depth);
            } else {
                return -WIN_SCORE + (MAX_DEPTH - depth);
            }
        }
        
        // Recursive call
        int score = minimax(player, depth - 1, alpha, beta, !is_maximizing, new_hash);
        
        // Undo move
        board.undo(move.row, move.col);
        
        // Update best
        if (is_maximizing) {
            if (score > best_score) {
                best_score = score;
                best_row = move.row;
                best_col = move.col;
            }
            alpha = std::max(alpha, score);
        } else {
            if (score < best_score) {
                best_score = score;
                best_row = move.row;
                best_col = move.col;
            }
            beta = std::min(beta, score);
        }
        
        // Alpha-beta cutoff
        if (beta <= alpha) {
            killer_moves.add(move.row, move.col, depth);
            break;
        }
    }
    
    // Store in TT
    int flag = (best_score <= alpha) ? 2 : (best_score >= beta) ? 1 : 0;
    tt.store(hash_key, depth, best_score, best_row, best_col, flag);
    
    return best_score;
}

} // namespace gomoku

// C-style API implementation
using namespace gomoku;

extern "C" {

void* gomoku_create_engine() {
    return new AIEngine();
}

void gomoku_destroy_engine(void* engine) {
    delete static_cast<AIEngine*>(engine);
}

void gomoku_set_board(void* engine, const int8_t* grid, int size) {
    AIEngine* ai = static_cast<AIEngine*>(engine);
    if (size != TOTAL_CELLS) return;
    
    std::copy(grid, grid + size, ai->board.grid.begin());
    
    // Count moves
    int count = 0;
    for (int i = 0; i < size; ++i) {
        if (grid[i] != EMPTY) count++;
    }
    ai->board.move_count = count;
}

void gomoku_find_best_move(void* engine, int player, int max_depth, 
                           double time_limit, int* out_row, int* out_col, int* out_score) {
    AIEngine* ai = static_cast<AIEngine*>(engine);
    Player p = (player == 1) ? BLACK : WHITE;
    
    Move best = ai->find_best_move(p, max_depth, time_limit);
    
    *out_row = best.row;
    *out_col = best.col;
    *out_score = best.score;
}

uint64_t gomoku_get_nodes_searched(void* engine) {
    return static_cast<AIEngine*>(engine)->nodes_searched;
}

double gomoku_get_search_time(void* engine) {
    return static_cast<AIEngine*>(engine)->search_time;
}

} // extern "C"
