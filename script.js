// script.js

// — Constants —
const EMPTY = '.';
const PLAYER_ONE = '🤖';
const PLAYER_TWO = '👾';
const VALID_CELLS = [EMPTY, PLAYER_ONE, PLAYER_TWO];

// Winning‐line index sets
const WIN_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
];

// Move outcomes
const MoveOutcome = {
    WIN: 'win',
    DRAW: 'draw',
    LOSS: 'loss',
    NEUTRAL: 'neutral',
};

// — ValueTable: 3⁹ states → value, serializable —
class ValueTable {
    #table = new Map();

    constructor(initial) {
        if (initial) {
            this.#table = new Map(Object.entries(initial));
        } else {
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
                const v = (() => {
                    if (TicTacToe.isWin(board, PLAYER_TWO)) return 0.0;
                    if (TicTacToe.isWin(board, PLAYER_ONE)
                        || TicTacToe.isDraw(board)) return 1.0;
                    return 0.5;
                })();
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
            throw new Error(`Key ${key} does not exist`);
        }
        return this.#table.get(key);
    }

    set(board, val) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Key ${key} does not exist`);
        }
        this.#table.set(key, val);
    }
}

// — Tabular Epsilon‑Greedy Agent —
class TabularEpsilonGreedyAgent {
    #table;

    constructor(initial) {
        this.#table = new ValueTable(initial);
    }

    playMove(board) {
        const values = new Map();
        for (let i = 0; i < board.length; i++) {
            if (board[i] === EMPTY) {
                const b2 = [...board];
                b2[i] = PLAYER_ONE;
                values.set(i, this.#table.get(b2));
            }
        }

        const eps = 0.1, lr = 0.5;
        const entries = [...values.entries()];
        const [gIdx, gVal] = entries.reduce(
            ([bestI, bestV], [i, v]) => v > bestV ? [i, v] : [bestI, bestV],
            entries[0]
        );

        if (values.size > 1 && Math.random() < eps) {
            const nonGreedy = entries.filter(([i]) => i !== gIdx);
            return nonGreedy[Math.floor(Math.random() * nonGreedy.length)][0];
        }

        const curVal = this.#table.get(board);
        this.#table.set(board, curVal + lr * (gVal - curVal));
        return gIdx;
    }

    exportTable() {
        return this.#table.toObject();
    }
}

// — Naive Agent for PLAYER_TWO —
class NaiveAgent {
    playMove(board) {
        for (let i = 0; i < 9; i++) {
            if (board[i] === EMPTY
                && TicTacToe.evaluateMove(board, i, PLAYER_TWO) === MoveOutcome.WIN) {
                return i;
            }
        }
        const avail = board.map((c, i) => c === EMPTY ? i : null)
            .filter(i => i !== null);
        return avail[Math.floor(Math.random() * avail.length)];
    }
}

// — Main TicTacToe Class —
class TicTacToe {
    #board;
    #isGameOver;
    #cells = [];
    #players = [];
    #current = 0;

    constructor() {
        this.boardEl = document.getElementById('board');
        this.msgEl = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');
        this.p2Select = document.getElementById('player2Select');
        this.exportBtn = document.getElementById('exportEpsilon');
        this.importBtn = document.getElementById('importEpsilon');
        this.importFile = document.getElementById('importEpsilonFile');
        this.statusEl = document.getElementById('statusEpsilon');

        this.epsilonData = null;

        this.resetBtn.addEventListener('click', () => this.init());
        this.exportBtn.addEventListener('click', e => { e.preventDefault(); this._export(); });
        this.importBtn.addEventListener('click', e => { e.preventDefault(); this.importFile.click(); });
        this.importFile.addEventListener('change', e => {
            const f = e.target.files[0];
            if (f) this._import(f);
            e.target.value = '';
        });

        this.init();
    }

    init() {
        const p1 = {
            type: 'AGENT',
            logical: PLAYER_ONE,
            display: PLAYER_ONE,
            agent: new TabularEpsilonGreedyAgent(this.epsilonData)
        };
        const p2 = this.p2Select.value === 'HUMAN'
            ? { type: 'HUMAN', logical: PLAYER_TWO, display: PLAYER_TWO }
            : { type: 'AGENT', logical: PLAYER_TWO, display: PLAYER_TWO, agent: new NaiveAgent() };

        this.#players = [p1, p2];
        this.#board = Array(9).fill(EMPTY);
        this.#isGameOver = false;
        this.#current = Math.random() < 0.5 ? 0 : 1;

        this.boardEl.replaceChildren();
        this.#cells = this.#board.map((_, i) => {
            const btn = document.createElement('button');
            btn.className = 'cell';
            btn.dataset.index = i;
            btn.disabled = false;
            btn.addEventListener('click', e => this._onClick(e));
            this.boardEl.appendChild(btn);
            return btn;
        });

        this.statusEl.textContent = '';

        const cur = this.#players[this.#current];
        if (cur.type === 'AGENT') {
            this.msgEl.textContent = 'Agent starts';
            setTimeout(() => this._agentMove(), 10);
        } else {
            this.msgEl.textContent = 'Your turn';
        }
    }

    _onClick(e) {
        if (this.#isGameOver) return;
        const i = +e.currentTarget.dataset.index;
        const p = this.#players[this.#current];
        if (p.type !== 'HUMAN' || this.#board[i] !== EMPTY) return;
        this._commit(i, p);
        if (!this._checkEnd(p)) this._next();
    }

    _agentMove() {
        if (this.#isGameOver) return;
        const p = this.#players[this.#current];
        const i = p.agent.playMove([...this.#board]);
        this._commit(i, p);
        if (!this._checkEnd(p)) this._next();
    }

    _commit(i, p) {
        this.#board[i] = p.logical;
        const btn = this.#cells[i];
        btn.textContent = p.display;
        btn.disabled = true;
    }

    _checkEnd(p) {
        if (TicTacToe.isWin(this.#board, p.logical)) {
            this.#isGameOver = true;
            const line = WIN_LINES.find(l => l.every(i => this.#board[i] === p.logical));
            if (line) line.forEach(i => this.#cells[i].classList.add('win'));
            this.msgEl.textContent = p.type === 'HUMAN' ? 'You win!' : 'Agent wins!';
            return true;
        }
        if (TicTacToe.isDraw(this.#board)) {
            this.#isGameOver = true;
            this.msgEl.textContent = "It's a draw!";
            return true;
        }
        return false;
    }

    _next() {
        this.#current = 1 - this.#current;
        const nxt = this.#players[this.#current];
        if (nxt.type === 'AGENT') {
            this.msgEl.textContent = 'Agent thinking…';
            setTimeout(() => this._agentMove(), 300);
        } else {
            this.msgEl.textContent = 'Your turn';
        }
    }

    _export() {
        const data = JSON.stringify(this.#players[0].agent.exportTable(), null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'epsilon-agent.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        this.statusEl.textContent = '✔ Table exported';
    }

    _import(file) {
        const reader = new FileReader();
        reader.onload = () => {
            try {
                this.epsilonData = JSON.parse(reader.result);
                this.#players[0].agent = new TabularEpsilonGreedyAgent(this.epsilonData);
                this.statusEl.textContent = '✔ Table imported';
            } catch {
                this.statusEl.textContent = '✖ Invalid JSON';
            }
        };
        reader.onerror = () => {
            this.statusEl.textContent = '✖ Read error';
        };
        reader.readAsText(file);
    }

    static isWin(board, sym) {
        return WIN_LINES.some(line => line.every(i => board[i] === sym));
    }

    static isDraw(board) {
        return board.every(c => c !== EMPTY)
            && !TicTacToe.isWin(board, PLAYER_ONE)
            && !TicTacToe.isWin(board, PLAYER_TWO);
    }

    static evaluateMove(board, idx, sym) {
        if (board[idx] !== EMPTY) throw new Error('Cell occupied');
        const b2 = [...board]; b2[idx] = sym;
        if (TicTacToe.isWin(b2, sym)) return MoveOutcome.WIN;
        if (TicTacToe.isDraw(b2)) return MoveOutcome.DRAW;
        const opp = sym === PLAYER_ONE ? PLAYER_TWO : PLAYER_ONE;
        for (let i = 0; i < 9; i++) {
            if (b2[i] === EMPTY) {
                const b3 = [...b2]; b3[i] = opp;
                if (TicTacToe.isWin(b3, opp)) return MoveOutcome.LOSS;
            }
        }
        return MoveOutcome.NEUTRAL;
    }
}

// Start the game
new TicTacToe();
