const HUMAN = '😁';
const COMPUTER = '🤖';

// Immutable list of all winning triples
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

class ValueTable {
    #table;
    constructor() {
        this.#table = new Map();

        // NOTE: Using "base-N enumeration" to find all possible combinations.
        //       There are potentially smarter things we can do 
        //       (e.g. do not consider invalid combinations that aren't possible),
        //       but not worrying about that now.

        // there are 3 possible states, so we are doing base-3
        const totalStates = 3 ** 9;
        const nums = [0, 0, 0, 0, 0, 0, 0, 0, -1];

        // TODO: "." should probably be a named character and replace null,
        //       since we're using it in serialize as well
        const digitMap = new Map()
        digitMap.set(0, null);
        digitMap.set(1, HUMAN);
        digitMap.set(2, COMPUTER);

        // first we initialize all states to 0.5
        for (let _ = 0; _ < totalStates; ++_) {
            // if (_ > 10) break;
            let i = nums.findLastIndex((el) => el <= 2)
            nums[i] += 1;
            while (nums[i] == 3) {
                // execute carries
                nums[i] = 0;
                i -= 1;
                nums[i] += 1;
            }

            let board = nums.map(d => digitMap.get(d))
            let estimatedValue = 0.5;
            if (TicTacToe.isWin(board, HUMAN)) {
                estimatedValue = 0.0;
            } else if (TicTacToe.isWin(board, COMPUTER) || TicTacToe.isDraw(board)) {
                estimatedValue = 1.0
            }

            this.#table.set(ValueTable.serialize(board), estimatedValue);
        }
    }

    // serialize [null, 😁, 🤖, ...] -> '.😁🤖......'
    static serialize(board) {
        return board.map(c => c === HUMAN ? HUMAN : c === COMPUTER ? COMPUTER : '.').join('')
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

class TicTacToe {
    // private game state
    #boardState;
    #isGameOver;
    #cells = [];
    // TODO: make this an agent function that can be selected
    //       rather than expose the impl detail of using a table
    #agentValueTable;

    constructor() {
        this.boardElement = document.getElementById('board');
        this.messageElement = document.getElementById('message');
        this.resetBtn = document.getElementById('reset');

        this.resetBtn.addEventListener('click', () => this.init());
        window.addEventListener('DOMContentLoaded', () => this.init());

        this.#agentValueTable = new ValueTable();
    }

    init() {
        this.#boardState = Array(9).fill(null);
        this.#isGameOver = false;
        this.currentPlayer = Math.random() < 0.5 ? HUMAN : COMPUTER;
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

        if (this.currentPlayer === COMPUTER) {
            this._makeComputerMove();
        }
    }

    onCellClick(e) {
        const idx = Number(e.currentTarget.dataset.index);
        if (this.#boardState[idx] || this.#isGameOver || this.currentPlayer !== HUMAN)
            return;

        this.playMove(idx, HUMAN);
        if (this.checkEnd(HUMAN)) return;

        this.currentPlayer = COMPUTER;
        this._makeComputerMove();
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

    _makeComputerMove() {
        const idx = this.getComputerMove([...this.#boardState]);
        if (idx < 0) return;
        this.playMove(idx, COMPUTER);
        if (this.checkEnd(COMPUTER)) return;
        this.currentPlayer = HUMAN;
        this.messageElement.textContent = "Your turn";
    }

    // ——— instance AI hook (you can override this in a subclass) ———
    getNaiveMove(board) {
        // look for immediate win
        for (let i = 0; i < 9; i++) {
            if (board[i] === null && TicTacToe.evaluateMove(board, i, COMPUTER) === 'win') {
                return i;
            }
        }
        // otherwise first empty
        return board.findIndex(c => c === null);
    }
    getComputerMove(board) {
        let values = new Map();
        for (let i = 0; i < board.length; i++) {
            if (board[i] != null) {
                continue;
            }
            let possibleBoard = [...board];
            possibleBoard[i] = COMPUTER;

            values.set(i, this.#agentValueTable.get(possibleBoard));
        }

        const maxEntry = Array.from(values.entries()).reduce((max, entry) => entry[1] > max[1] ? entry : max);

        let currentVal = this.#agentValueTable.get(board);
        console.log("currentVal", currentVal);
        let lr = 0.5;
        let eps = 0.2;
        let p = Math.random();
        console.log("p", p);
        if (1 - eps < p) {
            console.log("explore");
            // exploration move
            //
            // TODO: this might actually select the greedy value
            //       as we don't filter it, but i'm tired and
            //       don't care rn
            const entries = Array.from(values.entries());
            const randomIndex = Math.floor(Math.random() * entries.length);
            const [cellIdx, _] = entries[randomIndex];
            return cellIdx;
        }

        this.#agentValueTable.set(board, currentVal + lr * (maxEntry[1] - currentVal));
        console.log("exploit: updatedVal", this.#agentValueTable.get(board));
        return maxEntry[0];
    }

    static isWin(board, player) {
        return WIN_LINES.some(line => line.every(i => board[i] === player));
    }

    static isDraw(board) {
        return board.every(cell => cell !== null)
            && !TicTacToe.isWin(board, HUMAN)
            && !TicTacToe.isWin(board, COMPUTER);
    }

    /**
     * Simulate placing `player` at `idx` on a clone of `board`.
     * Returns 'win'|'draw'|'loss'|'neutral' for that hypothetical move.
     */
    static evaluateMove(board, idx, player) {
        if (board[idx] !== null) {
            throw new Error(`Cell ${idx} is already occupied`);
        }
        const b2 = [...board];
        b2[idx] = player;

        if (TicTacToe.isWin(b2, player)) return MoveOutcome.WIN;
        if (TicTacToe.isDraw(b2)) return MoveOutcome.DRAW;

        const opp = player === HUMAN ? COMPUTER : HUMAN;
        for (let i = 0; i < 9; i++) {
            if (b2[i] === null) {
                const b3 = [...b2];
                b3[i] = opp;
                if (TicTacToe.isWin(b3, opp)) return MoveOutcome.LOSS;
            }
        }
        return MoveOutcome.NEUTRAL;
    }
}

new TicTacToe();
