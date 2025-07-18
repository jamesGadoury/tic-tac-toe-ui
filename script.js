const HUMAN = Object.freeze('😁');
const AGENT = Object.freeze('🤖');
const EMPTY = Object.freeze('.');

const VALID_CELLS = Object.freeze([EMPTY, HUMAN, AGENT]);

const WIN_LINES = Object.freeze([
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  // rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  // cols
    [0, 4, 8], [2, 4, 6]            // diagonals
]);

const MoveOutcome = Object.freeze({
    WIN: 'win',
    DRAW: 'draw',
    LOSS: 'loss',
    NEUTRAL: 'neutral',
});

class NaiveAgent {
    playMove(board) {
        // look for immediate win
        for (let i = 0; i < 9; i++) {
            if (board[i] === EMPTY && TicTacToe.evaluateMove(board, i, AGENT) === 'win') {
                return i;
            }
        }

        const availableMoves = board
            .map((cell, index) => cell === EMPTY ? index : null)
            .filter(index => index !== null);

        if (availableMoves.length === 0) {
            throw new Error("No available moves");
        }
        return availableMoves[Math.floor(Math.random() * availableMoves.length)];
    }
}

class ValueTable {
    #table = new Map();
    constructor() {
        // NOTE: Using "base-N enumeration" to find all possible combinations.
        //       There are potentially smarter things we can do 
        //       (e.g. do not consider invalid combinations that aren't possible),
        //       but not worrying about that now.

        // there are 3 possible states, so we are doing base-3
        const totalStates = 3 ** 9;
        // we initialize last element to -1 just so first
        // loop updates it to 0 as our first state
        const nums = [0, 0, 0, 0, 0, 0, 0, 0, -1];

        for (let _ = 0; _ < totalStates; ++_) {
            let i = nums.findLastIndex((el) => el <= 2)
            nums[i] += 1;

            while (nums[i] == 3) {
                // execute carries
                nums[i] = 0;
                nums[--i] += 1;
            }

            const board = nums.map(num => VALID_CELLS[num])

            const estimatedValue = (() => {
                if (TicTacToe.isWin(board, HUMAN)) {
                    return 0.0;
                } else if (TicTacToe.isWin(board, AGENT) || TicTacToe.isDraw(board)) {
                    return 1.0;
                }
                return 0.5;
            })();

            this.#table.set(ValueTable.serialize(board), estimatedValue);
        }
    }

    // validate & serialize [.,😁,🤖,.,.,.,.,.,.] -> '.😁🤖......'
    static serialize(board) {
        if (board.some((cell) => !VALID_CELLS.includes(cell))) {
            throw new Error(`Board ${board} has 1 or more invalid cells. Valid cells are: ${VALID_CELLS}`);
        }
        return board.join('');
    }

    get(board) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            console.log(this.#table);
            throw new Error(`Key ${key} does not exist in ValueTable`);
        }
        return this.#table.get(key);
    }

    set(board, value) {
        const key = ValueTable.serialize(board);
        if (!this.#table.has(key)) {
            throw new Error(`Key ${key} does not exist in ValueTable`);
        }
        this.#table.set(key, value);
    }
}

class TabularEpsilonGreedyAgent {
    #valueTable = new ValueTable();

    playMove(board) {
        const values = (() => {
            let values = new Map();
            for (let i = 0; i < board.length; i++) {
                if (board[i] != EMPTY) {
                    continue;
                }
                const possibleBoard = [
                    ...board.slice(0, i),
                    AGENT,
                    ...board.slice(i + 1)
                ];

                values.set(i, this.#valueTable.get(possibleBoard));
            }
            return values;
        })();

        // TODO: Make configurable
        const eps = 0.1;

        // NOTE: P(X=exploitation) = 1 - ε .
        //       P(X=exploration) = ε;

        // find the greedy action (highest value)
        const entries = Array.from(values.entries()); // [ [cellIdx, val], … ]
        const [greedyIdx, greedyVal] = entries.reduce(
            ([bestIdx, bestVal], [idx, val]) =>
                val > bestVal ? [idx, val] : [bestIdx, bestVal],
            entries[0]
        );

        // if there’s more than one action and we “explore” with prob. ε
        if (values.size > 1 && Math.random() < eps) {
            // exploration move

            // filter out the greedy move so we definitely explore something else
            const nonGreedy = entries.filter(([idx]) => idx !== greedyIdx);
            const randomPick = nonGreedy[
                Math.floor(Math.random() * nonGreedy.length)
            ];
            return randomPick[0];
        }

        // TODO: make configurable
        const lr = 0.5;

        const currentVal = this.#valueTable.get(board);
        this.#valueTable.set(board, currentVal + lr * (greedyVal - currentVal));
        return greedyIdx;
    }
}

class TicTacToe {
    #boardState;
    #isGameOver;
    #cells = [];
    // TODO: make configurable
    #agent = new TabularEpsilonGreedyAgent();

    constructor() {
        this.boardElement = document.getElementById('board');
        this.messageElement = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');

        this.resetBtn.addEventListener('click', () => this.init());
        window.addEventListener('DOMContentLoaded', () => this.init());
    }

    init() {
        this.#boardState = Array(9).fill(EMPTY);
        this.#isGameOver = false;
        this.currentPlayer = Math.random() < 0.5 ? HUMAN : AGENT;
        this.messageElement.textContent =
            this.currentPlayer === HUMAN ? "You start!" : "Computer starts!";

        this.boardElement.replaceChildren();
        const frag = document.createDocumentFragment();
        this.#cells = [];

        this.#boardState.forEach((_, idx) => {
            const btn = document.createElement('button');
            btn.className = 'cell';
            btn.setAttribute('role', 'gridcell');
            btn.dataset.index = idx;
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            btn.addEventListener('click', e => this.onCellClick(e));
            frag.appendChild(btn);
            this.#cells[idx] = btn;
        });

        this.boardElement.replaceChildren(frag);

        if (this.currentPlayer === AGENT) {
            this._makeAgentMove();
        }
    }

    onCellClick(e) {
        const idx = Number(e.currentTarget.dataset.index);
        if (this.#boardState[idx] != EMPTY || this.#isGameOver || this.currentPlayer !== HUMAN) {
            return;
        }

        this.playMove(idx, HUMAN);
        if (this.checkEnd(HUMAN)) {
            return;
        }

        this.currentPlayer = AGENT;
        this._makeAgentMove();
    }

    playMove(idx, player) {
        this.#boardState[idx] = player;
        const btn = this.#cells[idx];
        btn.textContent = player;
        btn.disabled = true;
        btn.setAttribute('aria-disabled', 'true');
    }

    checkEnd(player) {
        if (TicTacToe.isWin(this.#boardState, player)) {
            this.#isGameOver = true;
            WIN_LINES
                .find(line => line.every(i => this.#boardState[i] === player))
                .forEach(i => this.#cells[i].classList.add('win'));
            this.messageElement.textContent = player == HUMAN ? 'You win 😁' : 'Computer wins 🤖';
            return true;
        }

        if (TicTacToe.isDraw(this.#boardState)) {
            this.#isGameOver = true;
            this.messageElement.textContent = "It's a draw!";
            return true;
        }

        return false;
    }

    _makeAgentMove() {
        const idx = this.#agent.playMove([...this.#boardState]);
        if (idx < 0) return;
        this.playMove(idx, AGENT);
        if (this.checkEnd(AGENT)) return;
        this.currentPlayer = HUMAN;
        this.messageElement.textContent = "Your turn";
    }

    static isWin(board, player) {
        return WIN_LINES.some(line => line.every(i => board[i] === player));
    }

    static isDraw(board) {
        return board.every(cell => cell !== EMPTY)
            && !TicTacToe.isWin(board, HUMAN)
            && !TicTacToe.isWin(board, AGENT);
    }

    /**
     * Simulate placing `player` at `idx` on a clone of `board`.
     * Returns 'win'|'draw'|'loss'|'neutral' for that hypothetical move.
     */
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

new TicTacToe();
