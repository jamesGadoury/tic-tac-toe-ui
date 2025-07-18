// ————————————————
//  Persistence helpers
// ————————————————
const STORAGE_KEY = 'TicTacToe:TabularEpsilonGreedy:v1';

// write a cookie (fallback if localStorage is full)
function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

// read a cookie
function getCookie(name) {
    return document.cookie
        .split('; ')
        .reduce((acc, pair) => {
            const [k, v] = pair.split('=');
            return k === name ? decodeURIComponent(v) : acc;
        }, '');
}

// ————————————————
//  Constants & Utilities
// ————————————————
const HUMAN = '😁';
const AGENT = '🤖';
const EMPTY = '.';
const VALID_CELLS = [EMPTY, HUMAN, AGENT];

const WIN_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
];

const MoveOutcome = {
    WIN: 'win', DRAW: 'draw', LOSS: 'loss', NEUTRAL: 'neutral'
};

// ————————————————
//  ValueTable can be (de)serialized
// ————————————————
class ValueTable {
    #table = new Map();

    // If initialData is an object-of-entries, use it; else build fresh
    constructor(initialData) {
        if (initialData) {
            this.#table = new Map(Object.entries(initialData));
        } else {
            // build all 3^9 states
            const total = 3 ** 9;
            const nums = [0, 0, 0, 0, 0, 0, 0, 0, -1];
            for (let k = 0; k < total; k++) {
                let i = nums.findLastIndex(n => n <= 2);
                nums[i]++;
                while (nums[i] === 3) { nums[i] = 0; i--; nums[i]++; }
                const board = nums.map(n => VALID_CELLS[n]);
                const v = TicTacToe.isWin(board, HUMAN) ? 0.0
                    : (TicTacToe.isWin(board, AGENT) || TicTacToe.isDraw(board)) ? 1.0
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
            throw new Error(`Missing key in table: ${key}`);
        }
        return this.#table.get(key);
    }

    set(board, v) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Missing key in table: ${key}`);
        }
        this.#table.set(key, v);
    }
}

// ————————————————
//  Epsilon‑Greedy Agent w/ save/load
// ————————————————
class TabularEpsilonGreedyAgent {
    #valueTable;

    // private ctor — use load() or new without args
    constructor(initialData) {
        this.#valueTable = new ValueTable(initialData);
    }

    // attempt to load from localStorage (or cookie); else fresh
    static load() {
        const raw = localStorage.getItem(STORAGE_KEY) || getCookie(STORAGE_KEY);
        if (raw) {
            try {
                const data = JSON.parse(raw);
                return new TabularEpsilonGreedyAgent(data);
            } catch (e) {
                console.warn('Could not parse saved table, starting fresh');
            }
        }
        return new TabularEpsilonGreedyAgent();
    }

    // save to localStorage; if that fails, to a cookie (365d expiry)
    save() {
        const obj = this.#valueTable.toObject();
        const str = JSON.stringify(obj);
        try {
            localStorage.setItem(STORAGE_KEY, str);
        } catch {
            setCookie(STORAGE_KEY, str, 365);
        }
    }

    playMove(board) {
        const values = new Map();
        for (let i = 0; i < board.length; i++) {
            if (board[i] === EMPTY) {
                const b2 = [...board]; b2[i] = AGENT;
                values.set(i, this.#valueTable.get(b2));
            }
        }
        const eps = 0.1, lr = 0.5;
        const entries = [...values.entries()];
        // greedy
        const [gI, gV] = entries.reduce(
            ([bi, bv], [i, v]) => v > bv ? [i, v] : [bi, bv],
            entries[0]
        );
        // explore?
        if (values.size > 1 && Math.random() < eps) {
            const non = entries.filter(([i]) => i !== gI);
            return non[Math.floor(Math.random() * non.length)][0];
        }
        // update
        const cur = this.#valueTable.get(board);
        this.#valueTable.set(board, cur + lr * (gV - cur));
        return gI;
    }
}

// ————————————————
//  NaiveAgent unchanged
// ————————————————
class NaiveAgent {
    playMove(board) {
        for (let i = 0; i < 9; i++) {
            if (board[i] === EMPTY
                && TicTacToe.evaluateMove(board, i, AGENT) === MoveOutcome.WIN) {
                return i;
            }
        }
        const avail = board.map((c, i) => c === EMPTY ? i : null).filter(i => i !== null);
        if (!avail.length) throw new Error('No moves');
        return avail[Math.floor(Math.random() * avail.length)];
    }
}

// ————————————————
//  Main TicTacToe class
// ————————————————
class TicTacToe {
    #boardState; #isGameOver; #cells = []; #players = []; #cur = 0;

    constructor() {
        this.boardElement = document.getElementById('board');
        this.msgElement = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');
        this.saveBtn = document.getElementById('saveTable');
        this.loadBtn = document.getElementById('loadTable');
        this.xSelect = document.getElementById('playerX');
        this.oSelect = document.getElementById('playerO');

        // remove HUMAN option from O
        for (let i = this.oSelect.options.length - 1; i >= 0; i--) {
            if (this.oSelect.options[i].value === 'HUMAN') {
                this.oSelect.remove(i);
            }
        }
        this.oSelect.value = 'NAIVE';

        // wire
        this.resetBtn.addEventListener('click', () => this.init());
        this.saveBtn.addEventListener('click', () => this._saveAgent());
        this.loadBtn.addEventListener('click', () => this._loadAgent());
        window.addEventListener('beforeunload', () => this._saveAgent());

        // start
        this.init();
    }

    init() {
        // build players
        const make = v => {
            if (v === 'HUMAN') return { type: 'HUMAN', symbol: HUMAN };
            if (v === 'NAIVE') return { type: 'AGENT', symbol: AGENT, agent: new NaiveAgent() };
            // EPS_GREEDY
            return { type: 'AGENT', symbol: AGENT, agent: TabularEpsilonGreedyAgent.load() };
        };
        this.#players = [make(this.xSelect.value), make(this.oSelect.value)];

        // reset board
        this.#boardState = Array(9).fill(EMPTY);
        this.#isGameOver = false;
        this.#cur = Math.random() < 0.5 ? 0 : 1;

        // render buttons
        this.boardElement.replaceChildren();
        this.#cells = this.#boardState.map((_, i) => {
            const b = document.createElement('button');
            b.className = 'cell'; b.dataset.index = i;
            b.disabled = false; b.addEventListener('click', e => this._onClick(e));
            this.boardElement.appendChild(b);
            return b;
        });

        // first move
        const p = this.#players[this.#cur];
        if (p.type === 'AGENT') {
            this.msgElement.textContent = `Agent starts`;
            setTimeout(() => this._agentMove(), 10);
        } else {
            this.msgElement.textContent = `Your turn`;
        }
    }

    // save current ε‑greedy agent (if active) to storage
    _saveAgent() {
        const p = this.#players.find(pl => pl.agent instanceof TabularEpsilonGreedyAgent);
        if (p) p.agent.save();
    }
    // load then re-init so new agent instance with loaded table is used
    _loadAgent() {
        this.init();
    }

    _onClick(e) {
        if (this.#isGameOver) return;
        const i = +e.target.dataset.index;
        const p = this.#players[this.#cur];
        if (p.type !== 'HUMAN' || this.#boardState[i] !== EMPTY) return;
        this._commit(i, p);
        if (!this._checkEnd(p)) this._next();
    }

    _agentMove() {
        if (this.#isGameOver) return;
        const p = this.#players[this.#cur];
        const i = p.agent.playMove([...this.#boardState]);
        this._commit(i, p);
        if (!this._checkEnd(p)) this._next();
    }

    _commit(i, p) {
        this.#boardState[i] = p.symbol;
        const b = this.#cells[i];
        b.textContent = p.symbol; b.disabled = true;
    }

    _checkEnd(p) {
        if (TicTacToe.isWin(this.#boardState, p.symbol)) {
            this.#isGameOver = true;
            // highlight
            WIN_LINES.find(l => l.every(i => this.#boardState[i] === p.symbol))
                .forEach(i => this.#cells[i].classList.add('win'));
            this.msgElement.textContent =
                p.type === 'HUMAN' ? 'You win!' : 'Agent wins!';
            return true;
        }
        if (TicTacToe.isDraw(this.#boardState)) {
            this.#isGameOver = true;
            this.msgElement.textContent = "It's a draw!";
            return true;
        }
        return false;
    }

    _next() {
        this.#cur = 1 - this.#cur;
        const p = this.#players[this.#cur];
        if (p.type === 'AGENT') {
            this.msgElement.textContent = 'Agent thinking…';
            setTimeout(() => this._agentMove(), 300);
        } else {
            this.msgElement.textContent = 'Your turn';
        }
    }

    static isWin(b, s) {
        return WIN_LINES.some(l => l.every(i => b[i] === s));
    }
    static isDraw(b) {
        return b.every(c => c !== EMPTY)
            && !TicTacToe.isWin(b, HUMAN)
            && !TicTacToe.isWin(b, AGENT);
    }
    static evaluateMove(b, i, p) {
        if (b[i] !== EMPTY) throw new Error('occupied');
        const b2 = [...b]; b2[i] = p;
        if (TicTacToe.isWin(b2, p)) return MoveOutcome.WIN;
        if (TicTacToe.isDraw(b2)) return MoveOutcome.DRAW;
        const opp = p === HUMAN ? AGENT : HUMAN;
        for (let j = 0; j < 9; j++) {
            if (b2[j] === EMPTY) {
                const b3 = [...b2]; b3[j] = opp;
                if (TicTacToe.isWin(b3, opp)) return MoveOutcome.LOSS;
            }
        }
        return MoveOutcome.NEUTRAL;
    }
}

// kick it off
new TicTacToe();
