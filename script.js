const EMPTY = '_'
const HUMAN = '😁';
const COMPUTER = '🤖';

// Immutable list of all winning triples
const WIN_LINES = Object.freeze([
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  // rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  // cols
    [0, 4, 8], [2, 4, 6]            // diagonals
]);

class TicTacToe {
    // private game state
    #boardState;
    #isGameOver;
    #cells = [];

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
        if (this.#boardState[idx] !== EMPTY || this.#isGameOver || this.currentPlayer !== HUMAN)
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

    getComputerMove(board) {
        // look for immediate win
        for (let i = 0; i < 9; i++) {
            if (board[i] === null && TicTacToe.evaluateMove(board, i, COMPUTER) === 'win') {
                return i;
            }
        }
        // otherwise select a random empty

        // NOTE: we use flatMap so that we can return empty arrays in the callback
        //       for non empty cells which will then get dropped by the flatten operation
        const emptyCellsIndices = board.flatMap((cell, idx) => cell === EMPTY ? [idx] : []);
        return emptyCellsIndices[Math.round(Math.random() * (emptyCellsIndices.length - 1))];
    }

    static isWin(board, player) {
        return WIN_LINES.some(line => line.every(i => board[i] === player));
    }

    static isDraw(board) {
        return board.every(cell => cell !== EMPTY)
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

        if (TicTacToe.isWin(b2, player)) return 'win';
        if (TicTacToe.isDraw(b2)) return 'draw';

        const opp = player === HUMAN ? COMPUTER : HUMAN;
        for (let i = 0; i < 9; i++) {
            if (b2[i] === null) {
                const b3 = [...b2];
                b3[i] = opp;
                if (TicTacToe.isWin(b3, opp)) return 'loss';
            }
        }
        return 'neutral';
    }
}

new TicTacToe();
