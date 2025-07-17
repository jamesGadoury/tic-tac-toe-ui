// script.js

// --- constants & state ---
const HUMAN    = 'X';
const COMPUTER = 'O';

let board;         // Array(9) of 'X' | 'O' | null
let isGameOver;    // boolean

// DOM refs
const boardEl   = document.getElementById('board');
const messageEl = document.getElementById('message');
const resetBtn  = document.getElementById('reset');
const cells     = [];  // will hold the 9 button elements

// --- setup & reset ---
function initGame() {
  board = Array(9).fill(null);
  isGameOver = false;
  messageEl.textContent = '';
  boardEl.innerHTML = '';    // wipe previous cells

  // create 9 buttons
  board.forEach((_, idx) => {
    const btn = document.createElement('button');
    btn.className = 'cell';
    btn.dataset.index = idx;
    btn.addEventListener('click', onCellClick);
    boardEl.append(btn);
    cells[idx] = btn;
  });
}

// reset button listener
resetBtn.addEventListener('click', initGame);

// --- user interaction ---
function onCellClick(e) {
  const idx = Number(e.currentTarget.dataset.index);
  if (board[idx] || isGameOver) return;

  playMove(idx, HUMAN);
  if (checkEnd(HUMAN)) return;

  const compIdx = getComputerMove(board);
  playMove(compIdx, COMPUTER);
  checkEnd(COMPUTER);
}

// apply move to state + UI
function playMove(idx, player) {
  board[idx] = player;
  const btn = cells[idx];
  btn.textContent = player;
  btn.disabled = true;
}

// --- win/draw logic ---
function checkEnd(player) {
  const winLine = findWinningLine(player);
  if (winLine) {
    isGameOver = true;
    winLine.forEach(i => cells[i].classList.add('win'));
    messageEl.textContent = `${player} wins!`;
    return true;
  }
  if (board.every(cell => cell)) {
    isGameOver = true;
    messageEl.textContent = "It's a draw!";
    return true;
  }
  return false;
}

function findWinningLine(player) {
  const lines = [
    [0,1,2],[3,4,5],[6,7,8],   // rows
    [0,3,6],[1,4,7],[2,5,8],   // cols
    [0,4,8],[2,4,6]            // diags
  ];
  return lines.find(line =>
    line.every(i => board[i] === player)
  );
}

// --- AI hook ---
/**
 * Returns the index (0–8) where the computer should play.
 * Right now it just picks the first empty cell.
 * To customize the AI, replace simpleAI() or
 * implement a new function and call it here.
 */
function getComputerMove(currentBoard) {
  return simpleAI(currentBoard);
}

function simpleAI(bd) {
  return bd.findIndex(cell => cell === null);
}

// --- initialize on page load ---
initGame();

