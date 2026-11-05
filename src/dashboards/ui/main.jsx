import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import '@fontsource/manrope/latin-400.css';
import '@fontsource/manrope/latin-500.css';
import '@fontsource/manrope/latin-600.css';
import '@fontsource/manrope/latin-700.css';
import '@fontsource/manrope/latin-800.css';
import App from './App.jsx';
import './styles.css';

const data=JSON.parse(document.getElementById('dados').textContent);
const root=createRoot(document.getElementById('root'));
flushSync(()=>root.render(<App data={data}/>));
