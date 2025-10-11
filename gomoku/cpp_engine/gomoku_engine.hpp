/**
 * Gomoku AI Engine - C++ Implementation
 * 
 * High-performance gomoku AI using minimax with alpha-beta pruning,
 * transposition table, and killer move heuristic.
 * 
 * Compiles to shared library (.dll for Windows, .so for Linux) for Python binding.
 */

#ifndef GOMOKU_ENGINE_HPP
#define GOMOKU_ENGINE_HPP

#include <array>
#include <cstdint>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <cstring>

namespace gomoku {

// Constants
constexpr int BOARD_SIZE = 15;
constexpr int TOTAL_CELLS = BOARD_SIZE * BOARD_SIZE;
constexpr int MAX_DEPTH = 10;
constexpr int INF = 1000000;
constexpr int WIN_SCORE = 100000;

// Player enum
enum Player : int8_t {
    EMPTY = 0,
    BLACK = 1,
    WHITE = 2
};

// Move structure
struct Move {
    int8_t row;
    int8_t col;
    int32_t score;
    
    Move() : row(-1), col(-1), score(0) {}
    Move(int8_t r, int8_t c, int32_t s = 0) : row(r), col(c), score(s) {}
};

// Board state
class Board {
public:
    std::array<int8_t, TOTAL_CELLS> grid;  // Flat array for cache efficiency
    int move_count;
    
    Board() : move_count(0) {
        std::fill(grid.begin(), grid.end(), EMPTY);
    }
    
    inline int8_t get(int row, int col) const {
        return grid[row * BOARD_SIZE + col];
    }
    
    inline void set(int row, int col, int8_t player) {
        grid[row * BOARD_SIZE + col] = player;
    }
    
    inline bool is_empty(int row, int col) const {
        return get(row, col) == EMPTY;
    }
    
    inline bool in_bounds(int row, int col) const {
        return row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE;
    }
    
    // Place stone
    void place(int row, int col, Player player) {
        set(row, col, player);
        move_count++;
    }
    
    // Undo move
    void undo(int row, int col) {
        set(row, col, EMPTY);
        move_count--;
    }
    
    // Check if position has winning line (5 in a row)
    bool check_win(int row, int col, Player player) const;
    
    // Quick evaluate (for move ordering)
    int quick_evaluate(int row, int col, Player player) const;
};

// Zobrist hashing
class ZobristHasher {
public:
    std::array<std::array<std::array<uint64_t, 2>, BOARD_SIZE>, BOARD_SIZE> table;
    
    ZobristHasher();
    
    uint64_t compute_hash(const Board& board) const;
    
    inline uint64_t update_hash(uint64_t current_hash, int row, int col, Player player) const {
        int player_idx = (player == BLACK) ? 0 : 1;
        return current_hash ^ table[row][col][player_idx];
    }
};

// Transposition Table entry
struct TTEntry {
    uint64_t hash_key;
    int16_t depth;
    int32_t score;
    int8_t best_row;
    int8_t best_col;
    int8_t flag;  // 0: exact, 1: lowerbound, 2: upperbound
    
    TTEntry() : hash_key(0), depth(0), score(0), best_row(-1), best_col(-1), flag(0) {}
};

// Transposition Table
class TranspositionTable {
public:
    static constexpr size_t TABLE_SIZE = 1 << 21;  // 2M entries (~48MB)
    std::array<TTEntry, TABLE_SIZE> table;
    
    void clear() {
        table.fill(TTEntry());
    }
    
    TTEntry* probe(uint64_t hash_key) {
        size_t index = hash_key % TABLE_SIZE;
        if (table[index].hash_key == hash_key) {
            return &table[index];
        }
        return nullptr;
    }
    
    void store(uint64_t hash_key, int depth, int score, int best_row, int best_col, int flag) {
        size_t index = hash_key % TABLE_SIZE;
        TTEntry& entry = table[index];
        
        // Always replace (simpler than depth-based)
        entry.hash_key = hash_key;
        entry.depth = depth;
        entry.score = score;
        entry.best_row = best_row;
        entry.best_col = best_col;
        entry.flag = flag;
    }
};

// Killer moves
class KillerMoves {
public:
    std::array<std::array<Move, 2>, MAX_DEPTH + 1> killers;
    
    void add(int row, int col, int depth) {
        if (depth > MAX_DEPTH) return;
        
        // Shift and add
        killers[depth][1] = killers[depth][0];
        killers[depth][0] = Move(row, col);
    }
    
    const std::array<Move, 2>& get(int depth) const {
        return killers[depth];
    }
    
    void clear() {
        for (auto& level : killers) {
            level.fill(Move());
        }
    }
};

// AI Engine
class AIEngine {
public:
    Board board;
    ZobristHasher zobrist;
    TranspositionTable tt;
    KillerMoves killer_moves;
    
    uint64_t nodes_searched;
    double search_time;
    
    AIEngine();
    
    // Find best move
    Move find_best_move(Player player, int max_depth, double time_limit);
    
    // Minimax with alpha-beta pruning
    int minimax(Player player, int depth, int alpha, int beta, bool is_maximizing, uint64_t hash_key);
    
    // Generate candidate moves
    std::vector<Move> generate_moves(Player player);
    
    // Evaluate board position
    int evaluate(Player player) const;
    
    // Evaluate single line (for pattern recognition)
    int evaluate_line(const std::array<int8_t, 5>& line, Player player) const;
};

} // namespace gomoku

// C-style API for Python binding
extern "C" {
    // Create/destroy engine
    void* gomoku_create_engine();
    void gomoku_destroy_engine(void* engine);
    
    // Set board state
    void gomoku_set_board(void* engine, const int8_t* grid, int size);
    
    // Find best move
    void gomoku_find_best_move(void* engine, int player, int max_depth, 
                               double time_limit, int* out_row, int* out_col, int* out_score);
    
    // Get statistics
    uint64_t gomoku_get_nodes_searched(void* engine);
    double gomoku_get_search_time(void* engine);
}

#endif // GOMOKU_ENGINE_HPP
