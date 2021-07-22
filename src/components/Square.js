import React from 'react';
import '../index.css'

// function component
function Square(props) {
    return (
      <button className="square" onClick={props.onClick}>
        {props.value}
      </button>
    );
}

export { Square };