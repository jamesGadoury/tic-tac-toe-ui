const HUMAN    = 'X';
const COMPUTER = 'O';

// Immutable list of all winning triples
const WIN_LINES = Object.freeze([
  [0,1,2], [3,4,5], [6,7,8],  // rows
  [0,3,6], [1,4,7], [2,5,8],  // cols
  [0,4,8], [2,4,6]            // diagonals
]);

class TicTacToe {
  #boardState;
  #isGameOver;
  #cells = [];

  constructor() {
    // grab DOM refs once
    this.boardElement   = document.getElementById('board');
    this.messageElement = document.getElementById('message');
    this.resetBtn       = document.getElementById('reset');

    // wire up reset and init on load
    this.resetBtn.addEventListener('click', () => this.init());
    window.addEventListener('DOMContentLoaded', () => this.init());
  }

  init() {
    // initialize state
    this.#boardState = Array(9).fill(null);
    this.#isGameOver = false;
    this.messageElement.textContent = '';

    // clear & rebuild board in one batch
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
  }

  onCellClick(e) {
    const idx = Number(e.currentTarget.dataset.index);
    if (this.#boardState[idx] || this.#isGameOver) return;

    this.playMove(idx, HUMAN);
    if (this.checkEnd(HUMAN)) return;

    const compIdx = this.getComputerMove([...this.#boardState]);
    if (compIdx >= 0) {
      this.playMove(compIdx, COMPUTER);
      this.checkEnd(COMPUTER);
    }
  }

  playMove(idx, player) {
    this.#boardState[idx] = player;
    const btn = this.#cells[idx];
    btn.textContent = player;
    btn.disabled = true;
    btn.setAttribute('aria-disabled', 'true');
  }

  checkEnd(player) {
    if (this.isWin(this.#boardState, player)) {
      this.#isGameOver = true;
      // highlight winning cells
      WIN_LINES
        .find(line => line.every(i => this.#boardState[i] === player))
        .forEach(i => this.#cells[i].classList.add('win'));
      this.messageElement.textContent = `${player} wins!`;
      return true;
    }

    if (this.isDraw(this.#boardState)) {
      this.#isGameOver = true;
      this.messageElement.textContent = "It's a draw!";
      return true;
    }

    return false;
  }

  /**
   * Check if `player` has a winning line on a given board array.
   */
  isWin(board, player) {
    return WIN_LINES.some(line => line.every(i => board[i] === player));
  }

  /**
   * Check if the board is full (and no one has won).
   */
  isDraw(board) {
    return board.every(cell => cell !== null)
        && !this.isWin(board, HUMAN)
        && !this.isWin(board, COMPUTER);
  }

  /**
   * Evaluate the outcome of placing `player` at `idx` on a *clone* of `board`.
   * Returns one of:
   *   'win'     — player immediately wins
   *   'draw'    — board becomes full without a win
   *   'loss'    — opponent can win on their next move
   *   'neutral' — none of the above (game continues)
   */
  evaluateMove(board, idx, player) {
    if (board[idx] !== null) {
      throw new Error(`Cell ${idx} is already occupied`);
    }

    // clone & apply
    const b2 = [...board];
    b2[idx] = player;

    // immediate win?
    if (this.isWin(b2, player)) {
      return 'win';
    }
    // immediate draw?
    if (this.isDraw(b2)) {
      return 'draw';
    }
    // could opponent win next?
    const opponent = (player === HUMAN ? COMPUTER : HUMAN);
    for (let i = 0; i < 9; i++) {
      if (b2[i] === null) {
        const b3 = [...b2];
        b3[i] = opponent;
        if (this.isWin(b3, opponent)) {
          return 'loss';
        }
      }
    }
    // otherwise the game goes on
    return 'neutral';
  }

  // ——— AI hook ———

  getComputerMove(board) {
    // pick any winning move first
    for (let i = 0; i < 9; i++) {
      if (board[i] === null && this.evaluateMove(board, i, COMPUTER) === 'win') {
        return i;
      }
    }
    // fallback trivial
    return board.findIndex(cell => cell === null);
  }
}

new TicTacToe();
