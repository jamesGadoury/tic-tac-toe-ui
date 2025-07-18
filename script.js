// —————————————————————————————————————
//  Constants & Helpers
// —————————————————————————————————————

// Symbols and valid cell states
const HUMAN = '😁';
const AGENT = '🤖';
const EMPTY = '.';
const VALID_CELLS = [EMPTY, HUMAN, AGENT];

// All winning‐line index combinations
const WIN_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
];

// Possible outcomes of a single‐move evaluation
const MoveOutcome = {
    WIN: 'win',
    DRAW: 'draw',
    LOSS: 'loss',
    NEUTRAL: 'neutral',
};

// A table of values for all 3^9 board states; optionally initialized
class ValueTable {
    #table = new Map();

    constructor(initialData) {
        if (initialData) {
            // import from a plain object
            this.#table = new Map(Object.entries(initialData));
        } else {
            // build fresh
            const total = 3 ** 9;
            const nums = [0, 0, 0, 0, 0, 0, 0, 0, -1];
            for (let k = 0; k < total; k++) {
                let i = nums.findLastIndex(n => n <= 2);
                nums[i]++;
                while (nums[i] === 3) {
                    nums[i] = 0;
                    i--;
                    nums[i]++;
                }
                const board = nums.map(n => VALID_CELLS[n]);
                const v = TicTacToe.isWin(board, HUMAN) ? 0.0
                    : TicTacToe.isWin(board, AGENT) || TicTacToe.isDraw(board) ? 1.0
                        : 0.5;
                this.#table.set(board.join(''), v);
            }
        }
    }

    toObject() {
        return Object.fromEntries(this.#table);
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
            throw new Error(`Missing key ${key}`);
        }
        return this.#table.get(key);
    }

    set(board, value) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Missing key ${key}`);
        }
        this.#table.set(key, value);
    }
}

// ε‑Greedy agent: holds a ValueTable and supports export
class TabularEpsilonGreedyAgent {
    #valueTable;
    constructor(initialData, id) {
        this.#valueTable = new ValueTable(initialData);
        this.id = id;
    }

    playMove(board) {
        const values = new Map();
        for (let i = 0; i < board.length; i++) {
            if (board[i] === EMPTY) {
                const b2 = [...board];
                b2[i] = AGENT;
                values.set(i, this.#valueTable.get(b2));
            }
        }

        const eps = 0.1;
        const lr = 0.5;
        const entries = [...values.entries()];
        const [gIdx, gVal] = entries.reduce(
            ([bestI, bestV], [i, v]) => v > bestV ? [i, v] : [bestI, bestV],
            entries[0]
        );

        if (values.size > 1 && Math.random() < eps) {
            const nonGreedy = entries.filter(([i]) => i !== gIdx);
            return nonGreedy[Math.floor(Math.random() * nonGreedy.length)][0];
        }

        const curVal = this.#valueTable.get(board);
        this.#valueTable.set(board, curVal + lr * (gVal - curVal));
        return gIdx;
    }

    exportTable() {
        return this.#valueTable.toObject();
    }
}

// A very simple agent: immediate win or random
class NaiveAgent {
    playMove(board) {
        for (let i = 0; i < 9; i++) {
            if (board[i] === EMPTY && TicTacToe.evaluateMove(board, i, AGENT) === MoveOutcome.WIN) {
                return i;
            }
        }
        const avail = board.map((c, i) => c === EMPTY ? i : null).filter(i => i !== null);
        if (avail.length === 0) throw new Error('No available moves');
        return avail[Math.floor(Math.random() * avail.length)];
    }
}

// —————————————————————————————————————
//  Main TicTacToe Class
// —————————————————————————————————————
class TicTacToe {
    #boardState;
    #isGameOver;
    #cells = [];
    #players = [];
    #currentPlayerIndex = 0;

    constructor() {
        // Element refs
        this.boardEl = document.getElementById('board');
        this.msgEl = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');
        this.xSelect = document.getElementById('playerX');
        this.oSelect = document.getElementById('playerO');
        this.agentSel = document.getElementById('agentSelect');
        this.exportBtn = document.getElementById('exportAgentBtn');
        this.importBtn = document.getElementById('importAgentBtn');
        this.importFile = document.getElementById('importAgentFile');
        this.statusEl = document.getElementById('agentStatus');

        // Make sure Player O has no "Human" option
        for (let i = this.oSelect.options.length - 1; i >= 0; i--) {
            if (this.oSelect.options[i].value === 'HUMAN') {
                this.oSelect.remove(i);
            }
        }
        this.oSelect.value = 'NAIVE';

        // Wire up controls
        this.resetBtn.addEventListener('click', () => this.init());
        this.exportBtn.addEventListener('click', e => {
            e.preventDefault();
            this._exportSelectedAgent();
        });
        this.importBtn.addEventListener('click', e => {
            e.preventDefault();
            this.importFile.click();
        });
        this.importFile.addEventListener('change', e => {
            const file = e.target.files[0];
            if (file) this._importSelectedAgent(file);
            e.target.value = '';
        });

        // Launch first game
        this.init();
    }

    init() {
        // Build the two players
        this.#players = [
            this._makePlayer(this.xSelect.value, 0),
            this._makePlayer(this.oSelect.value, 1),
        ];

        // Reset board
        this.#boardState = Array(9).fill(EMPTY);
        this.#isGameOver = false;
        this.#currentPlayerIndex = Math.random() < 0.5 ? 0 : 1;

        // Render cells
        this.boardEl.replaceChildren();
        this.#cells = this.#boardState.map((_, idx) => {
            const btn = document.createElement('button');
            btn.className = 'cell';
            btn.dataset.index = idx;
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            btn.addEventListener('click', e => this._onCellClick(e));
            this.boardEl.appendChild(btn);
            return btn;
        });

        // Clear status message
        this.statusEl.textContent = '';

        // First move
        const cur = this.#players[this.#currentPlayerIndex];
        if (cur.type === 'AGENT') {
            this.msgEl.textContent = `Agent (${this._agentLabel(cur.agent)}) starts`;
            setTimeout(() => this._agentMove(), 10);
        } else {
            this.msgEl.textContent = 'Your turn';
        }
    }

    _makePlayer(sel, idx) {
        if (sel === 'HUMAN') {
            return { type: 'HUMAN', symbol: HUMAN };
        }
        if (sel === 'NAIVE') {
            return { type: 'AGENT', symbol: AGENT, agent: new NaiveAgent() };
        }
        // EPS_GREEDY
        return {
            type: 'AGENT',
            symbol: AGENT,
            agent: new TabularEpsilonGreedyAgent(undefined, `player${idx}`)
        };
    }

    _exportSelectedAgent() {
        const idx = parseInt(this.agentSel.value, 10);
        const p = this.#players[idx];
        if (!(p.agent instanceof TabularEpsilonGreedyAgent)) {
            this.statusEl.textContent = `✖ Player ${idx === 0 ? 'X' : 'O'} isn’t ε‑greedy`;
            return;
        }
        const data = p.agent.exportTable();
        const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tic-tac-toe-agent${idx}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.statusEl.textContent = `✔ Exported Player ${idx === 0 ? 'X' : 'O'} table`;
    }

    _importSelectedAgent(file) {
        const idx = parseInt(this.agentSel.value, 10);
        const sel = idx === 0 ? this.xSelect.value : this.oSelect.value;
        if (sel !== 'EPS_GREEDY') {
            this.statusEl.textContent = `✖ Player ${idx === 0 ? 'X' : 'O'} isn’t ε‑greedy`;
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            try {
                const obj = JSON.parse(reader.result);
                this.#players[idx].agent = new TabularEpsilonGreedyAgent(obj, `player${idx}`);
                this.statusEl.textContent = `✔ Imported table for Player ${idx === 0 ? 'X' : 'O'}`;
            } catch {
                this.statusEl.textContent = '✖ Invalid JSON file';
            }
        };
        reader.onerror = () => {
            this.statusEl.textContent = '✖ Error reading file';
        };
        reader.readAsText(file);
    }

    _onCellClick(e) {
        if (this.#isGameOver) return;
        const idx = Number(e.currentTarget.dataset.index);
        const cur = this.#players[this.#currentPlayerIndex];
        if (cur.type !== 'HUMAN' || this.#boardState[idx] !== EMPTY) return;
        this._commitMove(idx, cur);
        if (!this._checkEnd(cur)) this._nextTurn();
    }

    _agentMove() {
        if (this.#isGameOver) return;
        const cur = this.#players[this.#currentPlayerIndex];
        const idx = cur.agent.playMove([...this.#boardState]);
        this._commitMove(idx, cur);
        if (!this._checkEnd(cur)) this._nextTurn();
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
            const line = WIN_LINES.find(l => l.every(i => this.#boardState[i] === player.symbol));
            if (line) line.forEach(i => this.#cells[i].classList.add('win'));
            this.msgEl.textContent = player.type === 'HUMAN' ? 'You win!' : 'Agent wins!';
            return true;
        }
        if (TicTacToe.isDraw(this.#boardState)) {
            this.#isGameOver = true;
            this.msgEl.textContent = "It's a draw!";
            return true;
        }
        return false;
    }

    _nextTurn() {
        this.#currentPlayerIndex = 1 - this.#currentPlayerIndex;
        const next = this.#players[this.#currentPlayerIndex];
        if (next.type === 'AGENT') {
            this.msgEl.textContent = `Agent (${this._agentLabel(next.agent)}) thinking…`;
            setTimeout(() => this._agentMove(), 300);
        } else {
            this.msgEl.textContent = 'Your turn';
        }
    }

    _agentLabel(agent) {
        return agent instanceof NaiveAgent ? 'Naive' : 'ε‑Greedy';
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
