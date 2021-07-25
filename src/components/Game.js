import React, { useEffect, useState } from 'react';
import '../index.css';
import { Board } from './Board';
import { Button } from './Button';

const HUMAN_PLAYER_MARKER = 'X';
const AI_PLAYER_MARKER    = 'O';

function calculateWinner(squares) {
  const LINES = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
  ];
  for (let i = 0; i < LINES.length; i++) {
    const [a, b, c] = LINES[i];
    if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
      return squares[a];
    }
  }
  return null;
}

function calculateDraw(squares) {
  for (const square of squares) {
    if (!square) {
      return false;
    }
  }
  return true;
}

function statusOfBoard(squares) {
  const winner = calculateWinner(squares);

  if (winner) {
    return `Winner: ${winner}`;
  }

  const draw = calculateDraw(squares);
  if (draw) {
    return 'Draw';
  }

  return (currentPlayerIsAI(squares) ? 'Opponent AI turn: O' : 'Your turn: X');
}

function cornerWasPlayed(squares) {
  return squares[0] || squares[2] || squares[6] || squares[8];
}

// just pulled from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/random
function getRandomInt(min, max) { 
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min) + min); //The maximum is exclusive and the minimum is inclusive
}

function randomCornerPlay(squares) {
  const corners = [0, 2, 6, 8];
  const availableCorners = corners.filter(corner => !squares[corner]);
  if (availableCorners === undefined || availableCorners.length === 0) {
    return null; // todo error would likely be best, but don't want to deal with that complexity at this stage
  }
  return corners[getRandomInt(0, availableCorners.length)]
}

function generateAvailableSquares(squares) {
  let availableSquares = [];
  for (let i = 0; i < squares.length; ++i) {
    if (!squares[i]) {
      availableSquares.push(i);
    }
  }
  if (availableSquares === undefined || availableSquares.length === 0) {
    return null; // todo error would likely be best
  }
  return availableSquares;
}

function generateRandomPlay(squares) {
  const availableSquares = generateAvailableSquares(squares);
  return availableSquares[getRandomInt(0, availableSquares.length)];
}

function generateWinningOrRandomPlay(squares) {
  const availableSquares = generateAvailableSquares(squares);
  for (let availableSquare of availableSquares) {
    let squaresCopy = [...squares];
    squaresCopy[availableSquare] = AI_PLAYER_MARKER;
    if (calculateWinner(squaresCopy)) {
      return availableSquare;
    }
  }
  return generateRandomPlay(squares);
}

function easyAIPlay(squares) {
  return generateRandomPlay(squares);
}

function difficultAIPlay(squares) {
  // three condition action rules based on AI always going second
  if (moveNumber(squares) === 1) {
    if (cornerWasPlayed(squares)) {
      return 4; // this is the middle square
    }
    return randomCornerPlay(squares);
  }
  return generateWinningOrRandomPlay(squares);
}

function generateAIPlay(difficulty, squares) {
  return (difficulty === 'Easy' ? easyAIPlay(squares) : difficultAIPlay(squares));
}

function playerThisMove(move) {
  return (move % 2) === 0 ? HUMAN_PLAYER_MARKER : AI_PLAYER_MARKER;
}
function moveNumber(squares) { // todo moveNumber bad name -> movesPlayed
  return squares.filter(square => square).length;
}

function currentPlayerMarker(squares) {
  return playerThisMove(moveNumber(squares)); // todo playerThisMove -> markerThisMove
}

function currentPlayerIsAI(squares) {
  const moves = moveNumber(squares);
  return (moves % 2 !== 0 && moves !== 0);
}

function generateRowColumn(i) {
  return ["(0,0)", "(0,1)", "(0,2)", "(1,0)", "(1,1)", "(1,2)", "(2,0)", "(2,1)", "(2,2)"][i];
}

function play(history, move) {
  if (move === 0) {
    return "Game Start";
  }
  const history_before = history[move-1];
  const history_after  = history[move];
  
  for (let i = 0; i < history[0].squares.length; ++i) {
    if (!history_before.squares[i] && history_after.squares[i]) {
      const new_marker = history_after.squares[i];
      const player = new_marker === AI_PLAYER_MARKER ? 'Opponent AI' : 'You';
      return player + " played " + new_marker + " on " + generateRowColumn(i);
    }
  }
  console.log("No difference in history in play function!");
  return null; 
}

function Game() {
  const [history, setHistory] = useState([{
    squares: Array(9).fill(null),
  }]);

  const [difficulty, setDifficulty] = useState('Easy');

  const handleClick = (i) => {
    const current = history[history.length - 1];

    // replace data with a new copy, instead of mutating original data
    // React apparently loves immutability - see `pure components`
    // this helps React easily determine if changes have been made,
    // which helps to determine when a component requires re-rendering
    const squares = current.squares.slice();

    if (calculateWinner(squares) || squares[i] || currentPlayerIsAI(squares)) {
      // either there is already a winner, or someone is trying
      // to select a square that has already been picked, or
      // it isn't the player's turn
      return;
    }
    squares[i] = currentPlayerMarker(squares);

    setHistory(history.concat([{
      squares: squares
    }]));
  }
  
  useEffect(() => {
    const handleAIPlay = async (i) => {
      const current = history[history.length - 1];

      // replace data with a new copy, instead of mutating original data
      // React apparently loves immutability - see `pure components`
      // this helps React easily determine if changes have been made,
      // which helps to determine when a component requires re-rendering
      const squares = current.squares.slice();

      if (!currentPlayerIsAI(squares)) {
        console.log("handleAIPlay called while current player is human!!!");
      }

      // insert arbitrary sleep so that ai's response isn't instant
      await new Promise(r => setTimeout(r, 500)); 

      squares[i] = AI_PLAYER_MARKER;

      setHistory(history.concat([{
        squares: squares
      }]));
    }
    
    const squares = history[history.length-1].squares;
    if (playerThisMove(moveNumber(squares)) === HUMAN_PLAYER_MARKER || 
        calculateDraw(squares) || calculateWinner(squares)) {
      return;
    }
    handleAIPlay(generateAIPlay(difficulty, squares));
  }, [history]);


  const jumpTo = (move) => {
    setHistory(history.slice(0, move+1));
  }

  const changeDifficulty = () => {
    setDifficulty(difficulty === 'Easy' ? 'Hard' : 'Easy');
  }

  const squares = history[history.length-1].squares;
  const status = statusOfBoard(squares); 

  const moves = history.map((step, move) => {
    const description = play(history, move); 
    return (
      // we add a key to give React the ability to know
      // what components to update
      <li key={move} className="move-button"> 
        <Button
          text={description}
          onClick={() => jumpTo(move)}
        />
      </li>
    );
  });

  return (
    <div className="game">
      <div className="game-info">
        <Button
          text={difficulty}
          onClick={() => changeDifficulty()}
        />
      </div>
      <div className="game-board">
        <Board 
          squares={squares}
          onClick={(i) => handleClick(i)}
        />
      </div>
      <div className="game-info">
        <h3>{status}</h3>
        <ol>{moves}</ol>
      </div>
    </div>
  );
}

export { Game };