import React from 'react';
import '../index.css';
import { Title } from './Title';
import { Game } from './Game';

function App() {
   return (
      <div className='app'>
         <Title />
         <Game />
      </div>
   );
}

export { App };