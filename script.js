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
    const line = WIN_LINES.find(l => l.every(i => this.#boardState[i] === player));
    if (line) {
      this.#isGameOver = true;
      line.forEach(i => this.#cells[i].classList.add('win'));
      this.messageElement.textContent = `${player} wins!`;
      return true;
    }
    if (this.#boardState.every(cell => cell !== null)) {
      this.#isGameOver = true;
      this.messageElement.textContent = "It's a draw!";
      return true;
    }
    return false;
  }

  getComputerMove(board) {
    return this.simpleAI(board);
  }

  simpleAI(board) {
    // trivial: first empty
    return board.findIndex(cell => cell === null);
  }
}

new TicTacToe();
