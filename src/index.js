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

function nextPlayerMarker(currentPlayerMarker) {
  return currentPlayerMarker === 'X' ? 'O' : 'X';
}

class Board extends React.Component {
  renderSquare(i) {
    return (
      <Square 
        value={this.props.squares[i]}
        onClick={() => this.props.onClick(i)} 
      />
    ); // parantheses used so that Javascript doesn't insert a colon after return and break things
  }

  render() {
    return (
      <div>
        <div className="board-row">
          {this.renderSquare(0)}
          {this.renderSquare(1)}
          {this.renderSquare(2)}
        </div>
        <div className="board-row">
          {this.renderSquare(3)}
          {this.renderSquare(4)}
          {this.renderSquare(5)}
        </div>
        <div className="board-row">
          {this.renderSquare(6)}
          {this.renderSquare(7)}
          {this.renderSquare(8)}
        </div>
      </div>
    );
  }
}

class Game extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      history: [{
        squares: Array(9).fill(null),
      }],
      currentPlayerMarker: 'X',
      winner: null,
    }
  }

  handleClick(i) {
    const history = this.state.history;
    const current = history[history.length - 1];

    // replace data with a new copy, instead of mutating original data
    // React apparently loves immutability - see `pure components`
    // this helps React easily determine if changes have been made,
    // which helps to determine when a component requires re-rendering
    const squares = current.squares.slice();
    const winner  = this.state.winner;

    if (winner || squares[i]) {
      // either there is already a winner, or someone is trying
      // to select a square that has already been picked
      return;
    }

    squares[i] = this.state.currentPlayerMarker;

    const currentPlayerMarker = this.state.currentPlayerMarker;

    this.setState({
      history: history.concat([{
        squares: squares
      }]),
      currentPlayerMarker: nextPlayerMarker(currentPlayerMarker),
      winner: calculateWinner(squares)
    });
  }

  render() {
    const history = this.state.history;
    const current = history[history.length - 1];
    const status = ( this.state.winner ? 
      `Winner: ${this.state.winner}` :
      `Current player's turn: ${this.state.currentPlayerMarker}`
    );

    return (
      <div className="game">
        <div className="game-board">
          <Board 
            squares={current.squares}
            onClick={(i) => this.handleClick(i)}
          />
        </div>
        <div className="game-info">
          <div>{status}</div>
          <ol>{/* TODO */}</ol>
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
