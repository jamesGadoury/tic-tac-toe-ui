import React from 'react';
import '../index.css';
import { Square } from './Square';

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
      <div className="board">
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

export { Board };