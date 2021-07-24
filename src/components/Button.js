import React from 'react';
import '../index.css';
import { AwesomeButton } from "react-awesome-button";
import AwesomeButtonStyles from "react-awesome-button/src/styles/styles.scss";

function Button(props) {
  return (
    <AwesomeButton
      type="primary"
      ripple
      onPress={() => props.onClick()}
    >
     {props.text} 
    </AwesomeButton>
  );
}

export { Button };