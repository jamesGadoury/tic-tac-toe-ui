// Symbols and valid cell states
const HUMAN = Object.freeze('😁');
const AGENT = Object.freeze('🤖');
const EMPTY = Object.freeze('.');
const VALID_CELLS = Object.freeze([EMPTY, HUMAN, AGENT]);

// All win line combinations
const WIN_LINES = Object.freeze([
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // cols
    [0, 4, 8], [2, 4, 6],            // diagonals
]);

// Outcome enumeration
const MoveOutcome = Object.freeze({
    WIN: 'win',
    DRAW: 'draw',
    LOSS: 'loss',
    NEUTRAL: 'neutral',
});

// A naive agent: immediate win or random
class NaiveAgent {
    playMove(board) {
        // Check for immediate win
        for (let i = 0; i < 9; i++) {
            if (board[i] === EMPTY && TicTacToe.evaluateMove(board, i, AGENT) === MoveOutcome.WIN) {
                return i;
            }
        }
        // Otherwise pick randomly
        const avail = board
            .map((c, i) => (c === EMPTY ? i : null))
            .filter(i => i !== null);
        if (avail.length === 0) throw new Error("No available moves");
        return avail[Math.floor(Math.random() * avail.length)];
    }
}

// Table of values for all possible board states (3^9)
class ValueTable {
    #table = new Map();

    constructor() {
        const total = 3 ** 9;
        const nums = [0, 0, 0, 0, 0, 0, 0, 0, -1];
        for (let k = 0; k < total; k++) {
            // Increment in base-3
            let i = nums.findLastIndex(n => n <= 2);
            nums[i]++;
            while (nums[i] === 3) {
                nums[i] = 0;
                i--;
                nums[i]++;
            }
            const board = nums.map(n => VALID_CELLS[n]);
            const val = TicTacToe.isWin(board, HUMAN) ? 0.0
                : (TicTacToe.isWin(board, AGENT) || TicTacToe.isDraw(board)) ? 1.0
                    : 0.5;
            this.#table.set(board.join(''), val);
        }
    }

    static serialize(board) {
        if (board.some(c => !VALID_CELLS.includes(c))) {
            throw new Error(`Invalid board: ${board}`);
        }
        return board.join('');
    }

    get(board) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Key ${key} not in table`);
        }
        return this.#table.get(key);
    }

    set(board, v) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Key ${key} not in table`);
        }
        this.#table.set(key, v);
    }
}

// Epsilon-greedy agent that updates its table online
class TabularEpsilonGreedyAgent {
    #valueTable = new ValueTable();

    playMove(board) {
        const values = new Map();
        for (let i = 0; i < board.length; i++) {
            if (board[i] === EMPTY) {
                const b2 = [...board];
                b2[i] = AGENT;
                values.set(i, this.#valueTable.get(b2));
            }
        }

        const eps = 0.1, lr = 0.5;
        const entries = [...values.entries()];
        // Find greedy action
        const [gIdx, gVal] = entries.reduce(
            ([bestI, bestV], [i, v]) => v > bestV ? [i, v] : [bestI, bestV],
            entries[0]
        );

        // Explore?
        if (values.size > 1 && Math.random() < eps) {
            const nonG = entries.filter(([i]) => i !== gIdx);
            return nonG[Math.floor(Math.random() * nonG.length)][0];
        }

        // Update value of current state
        const cur = this.#valueTable.get(board);
        this.#valueTable.set(board, cur + lr * (gVal - cur));

        return gIdx;
    }
}

// Main game class
class TicTacToe {
    #boardState;
    #isGameOver;
    #cells = [];
    #players = [];
    #currentPlayerIndex = 0;

    constructor() {
        this.boardElement = document.getElementById('board');
        this.messageElement = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');
        this.playerXSelect = document.getElementById('playerX');
        this.playerOSelect = document.getElementById('playerO');

        // Ensure Player O can only be an agent
        for (let i = this.playerOSelect.options.length - 1; i >= 0; i--) {
            if (this.playerOSelect.options[i].value === 'HUMAN') {
                this.playerOSelect.remove(i);
            }
        }
        this.playerOSelect.value = 'NAIVE';

        this.resetBtn.addEventListener('click', () => this.init());

        // Start the first game immediately
        this.init();
    }

    init() {
        // Build players based on selectors
        const makePlayer = sel => {
            if (sel === 'HUMAN') {
                return { type: 'HUMAN', symbol: HUMAN };
            } else if (sel === 'NAIVE') {
                return { type: 'AGENT', symbol: AGENT, agent: new NaiveAgent() };
            } else {
                return { type: 'AGENT', symbol: AGENT, agent: new TabularEpsilonGreedyAgent() };
            }
        };

        this.#players = [
            makePlayer(this.playerXSelect.value),
            makePlayer(this.playerOSelect.value),
        ];

        // Reset game state
        this.#boardState = Array(9).fill(EMPTY);
        this.#isGameOver = false;
        this.#currentPlayerIndex = Math.random() < 0.5 ? 0 : 1;

        // Render board
        this.boardElement.replaceChildren();
        this.#cells = this.#boardState.map((_, idx) => {
            const btn = document.createElement('button');
            btn.className = 'cell';
            btn.dataset.index = idx;
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            btn.addEventListener('click', e => this.onCellClick(e));
            this.boardElement.appendChild(btn);
            return btn;
        });

        // Announce and possibly let agent move first
        const current = this.#players[this.#currentPlayerIndex];
        if (current.type === 'AGENT') {
            this.messageElement.textContent = `Agent (${this._agentName(current)}) starts`;
            setTimeout(() => this._makeAgentMove(), 10);
        } else {
            this.messageElement.textContent = 'Your turn';
        }
    }

    onCellClick(e) {
        if (this.#isGameOver) return;
        const idx = Number(e.currentTarget.dataset.index);
        const current = this.#players[this.#currentPlayerIndex];
        if (current.type !== 'HUMAN') return;
        if (this.#boardState[idx] !== EMPTY) return;

        this._commitMove(idx, current);
        if (this._checkEnd(current)) return;
        this._nextTurn();
    }

    _makeAgentMove() {
        if (this.#isGameOver) return;
        const current = this.#players[this.#currentPlayerIndex];
        const idx = current.agent.playMove([...this.#boardState]);
        this._commitMove(idx, current);
        if (this._checkEnd(current)) return;
        this._nextTurn();
    }

    _commitMove(idx, player) {
        this.#boardState[idx] = player.symbol;
        const btn = this.#cells[idx];
        btn.textContent = player.symbol;
        btn.disabled = true;
        btn.setAttribute('aria-disabled', 'true');
    }

    _checkEnd(player) {
        if (TicTacToe.isWin(this.#boardState, player.symbol)) {
            this.#isGameOver = true;
            // Highlight the winning line
            const winLine = WIN_LINES.find(line =>
                line.every(i => this.#boardState[i] === player.symbol)
            );
            if (winLine) {
                winLine.forEach(i => this.#cells[i].classList.add('win'));
            }
            this.messageElement.textContent =
                player.type === 'HUMAN'
                    ? 'You win!'
                    : `Agent (${this._agentName(player)}) wins!`;
            return true;
        }
        if (TicTacToe.isDraw(this.#boardState)) {
            this.#isGameOver = true;
            this.messageElement.textContent = "It's a draw!";
            return true;
        }
        return false;
    }

    _nextTurn() {
        this.#currentPlayerIndex = 1 - this.#currentPlayerIndex;
        const next = this.#players[this.#currentPlayerIndex];
        if (next.type === 'AGENT') {
            this.messageElement.textContent = `Agent (${this._agentName(next)}) thinking…`;
            setTimeout(() => this._makeAgentMove(), 300);
        } else {
            this.messageElement.textContent = 'Your turn';
        }
    }

    _agentName(player) {
        return player.agent instanceof NaiveAgent ? 'Naive' : 'Epsilon‑Greedy';
    }

    static isWin(board, player) {
        return WIN_LINES.some(line => line.every(i => board[i] === player));
    }

    static isDraw(board) {
        return board.every(c => c !== EMPTY)
            && !TicTacToe.isWin(board, HUMAN)
            && !TicTacToe.isWin(board, AGENT);
    }

    static evaluateMove(board, idx, player) {
        if (board[idx] !== EMPTY) {
            throw new Error(`Cell ${idx} is already occupied`);
        }
        const b2 = [...board];
        b2[idx] = player;
        if (TicTacToe.isWin(b2, player)) return MoveOutcome.WIN;
        if (TicTacToe.isDraw(b2)) return MoveOutcome.DRAW;

        const opp = player === HUMAN ? AGENT : HUMAN;
        for (let i = 0; i < 9; i++) {
            if (b2[i] === EMPTY) {
                const b3 = [...b2];
                b3[i] = opp;
                if (TicTacToe.isWin(b3, opp)) return MoveOutcome.LOSS;
            }
        }
        return MoveOutcome.NEUTRAL;
    }
}

// Start the game
new TicTacToe();
