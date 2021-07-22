import React from 'react';
import ReactDOM from 'react-dom';
import './index.css'

// function component
function Square(props) {
    return (
      <button className="square" onClick={props.onClick}>
        {props.value}
      </button>
    );
}

function Board(props)  {
  const renderSquare = (i) => {
    return (
      <Square 
        value={props.squares[i]}
        onClick={() => props.onClick(i)} 
      />
    ); // parantheses used so that Javascript doesn't insert a colon after return and break things
  }

  return (
    <div>
      <div className="board-row">
        {renderSquare(0)}
        {renderSquare(1)}
        {renderSquare(2)}
      </div>
      <div className="board-row">
        {renderSquare(3)}
        {renderSquare(4)}
        {renderSquare(5)}
      </div>
      <div className="board-row">
        {renderSquare(6)}
        {renderSquare(7)}
        {renderSquare(8)}
      </div>
    </div>
  );
}

function calculateDraw(squares) {
  for (const square of squares) {
    if (!square) {
      return false;
    }
  }
  return true;
}

function calculateWinner(squares) {
  const lines = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
  ];
  for (let i = 0; i < lines.length; i++) {
    const [a, b, c] = lines[i];
    if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
      return squares[a];
    }
  }
  return null;
}

function statusOfBoard(squares, currentPlayerMarker) {
  const winner = calculateWinner(squares);

  if (winner) {
    return `Winner: ${winner}`;
  }

  const draw = calculateDraw(squares);
  if (draw) {
    return 'Draw';
  }
  
  return `Current player's turn: ${currentPlayerMarker}`
}

function nextPlayerMarker(currentPlayerMarker) {
  return currentPlayerMarker === 'X' ? 'O' : 'X';
}

function playerThisMove(move) {
  return (move % 2) === 0 ? 'X' : 'O';
}

function currentPlayerIsAI(currentPlayerMarker) {
  return currentPlayerMarker === 'O';
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
  if (availableCorners === undefined || availableCorners.length == 0) {
    return null; // todo error would likely be best, but don't want to deal with that complexity at this stage
  }
  return corners[getRandomInt(0, availableCorners.length)]
}

function searchForBestPlay(squares) {
  // todo
}

function generateRandomPlay(squares) {
  let availableSquares = [];
  for (let i = 0; i < squares.length; ++i) {
    if (!squares[i]) {
      availableSquares.push(i);
    }
  }
  if (availableSquares === undefined || availableSquares.length == 0) {
    return null; // todo error would likely be best
  }
  return availableSquares[getRandomInt(0, availableSquares.length)];
}

function generateAIPlay(squares, moveNumber) {
  // three condition action rules based on AI always going second
  if (moveNumber === 1) {
    if (cornerWasPlayed(squares)) {
      return 4; // this is the middle square
    }
    return randomCornerPlay(squares);
  }
  return generateRandomPlay(squares);
}

class Game extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      history: [{
        squares: Array(9).fill(null),
      }],
      currentPlayerMarker: 'X',
      moveNumber: 0
    }
  }

  handleClick(i) {
    const currentPlayerMarker = this.state.currentPlayerMarker;
    const history = this.state.history.slice(0, this.state.moveNumber+1);
    const current = history[history.length - 1];

    // replace data with a new copy, instead of mutating original data
    // React apparently loves immutability - see `pure components`
    // this helps React easily determine if changes have been made,
    // which helps to determine when a component requires re-rendering
    const squares = current.squares.slice();

    if (calculateWinner(squares) || squares[i] || currentPlayerIsAI(currentPlayerMarker)) {
      // either there is already a winner, or someone is trying
      // to select a square that has already been picked, or
      // it isn't the player's turn
      return;
    }

    squares[i] = currentPlayerMarker;

    this.setState({
      history: history.concat([{
        squares: squares
      }]),
      currentPlayerMarker: nextPlayerMarker(currentPlayerMarker),
      moveNumber: history.length,
    }, () => {
      if (!calculateWinner(squares) && !calculateDraw(squares)) {
        this.handleAIPlay(generateAIPlay(squares, this.state.moveNumber)); // todo, really should be getting moveNumber from count of squares 
      }
    });

  }

  handleAIPlay(i) {
    const currentPlayerMarker = 'O';
    const history = this.state.history.slice(0, this.state.moveNumber+1);
    const current = history[history.length - 1];

    // replace data with a new copy, instead of mutating original data
    // React apparently loves immutability - see `pure components`
    // this helps React easily determine if changes have been made,
    // which helps to determine when a component requires re-rendering
    const squares = current.squares.slice();
    squares[i] = currentPlayerMarker;

    this.setState({
      history: history.concat([{
        squares: squares
      }]),
      currentPlayerMarker: nextPlayerMarker(currentPlayerMarker),
      moveNumber: history.length,
    });
  }

  jumpTo(move) {
    this.setState({
      moveNumber: move,
      currentPlayerMarker: playerThisMove(move)
    },() => {
      if (currentPlayerIsAI(this.state.currentPlayerMarker)) {
        const moveNumber = this.state.moveNumber;
        const history = this.state.history.slice(0, moveNumber+1);
        const squares = history[history.length - 1].squares;

        this.handleAIPlay(generateAIPlay(squares, moveNumber)); // todo, really should be getting moveNumber from count of squares 
      } 
    });
  }

  render() {
    const currentPlayerMarker = this.state.currentPlayerMarker;
    const history = this.state.history;
    const current = history[this.state.moveNumber];
    const squares = current.squares;
    const status = statusOfBoard(squares, currentPlayerMarker); 

    const moves = history.map((step, move) => {
      const desc = move ?
        `Go to move #${move}` :
        'Go to game start';

      return (
        // we add a key to give React the ability to know
        // what components to update
        <li key={move}> 
          <button onClick={() => this.jumpTo(move)}>{desc}</button>
        </li>
      );
    });

    return (
      <div className="game">
        <div className="game-board">
          <Board 
            squares={squares}
            onClick={(i) => this.handleClick(i)}
          />
        </div>
        <div className="game-info">
          <div>{status}</div>
          <ol>{moves}</ol>
        </div>
      </div>
    );
  }
}

// ========================================

ReactDOM.render(
  <Game />,
  document.getElementById('root')
);
