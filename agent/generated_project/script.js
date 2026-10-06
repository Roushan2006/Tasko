/* Calculator functionality and theme toggle */
(function() {
  'use strict';

  // Theme toggle functionality
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = themeToggle.querySelector('.theme-icon');

  // Load saved theme preference
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  themeToggle.addEventListener('click', function() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    themeToggle.setAttribute('aria-pressed', newTheme === 'dark');
  });

  function updateThemeIcon(theme) {
    if (theme === 'dark') {
      themeIcon.textContent = '☀️';
      themeIcon.classList.add('theme-icon--sun');
      themeIcon.classList.remove('theme-icon--moon');
      themeToggle.setAttribute('aria-pressed', 'true');
    } else {
      themeIcon.textContent = '🌙';
      themeIcon.classList.add('theme-icon--moon');
      themeIcon.classList.remove('theme-icon--sun');
      themeToggle.setAttribute('aria-pressed', 'false');
    }
  }

  // Calculator state
  let currentOperand = '0';
  let previousOperand = '';
  let operation = undefined;
  let history = [];

  // DOM Elements
  const currentOperandElement = document.getElementById('current-operand');
  const previousOperandElement = document.getElementById('previous-operand');
  const historyElement = document.getElementById('history');

  // Update display
  function updateDisplay() {
    currentOperandElement.textContent = currentOperand;
    previousOperandElement.textContent = previousOperand + (operation ? ` ${getOperationSymbol(operation)}` : '');
  }

  // Get operation symbol
  function getOperationSymbol(op) {
    switch (op) {
      case 'add': return '+';
      case 'subtract': return '−';
      case 'multiply': return '×';
      case 'divide': return '÷';
      default: return '';
    }
  }

  // Append number
  function appendNumber(number) {
    if (number === '.' && currentOperand.includes('.')) return;
    if (currentOperand === '0' && number !== '.') {
      currentOperand = number;
    } else {
      currentOperand += number;
    }
    updateDisplay();
  }

  // Choose operation
  function chooseOperation(op) {
    if (currentOperand === '') return;
    if (previousOperand !== '') {
      compute();
    }
    operation = op;
    previousOperand = currentOperand;
    currentOperand = '';
    updateDisplay();
  }

  // Compute
  function compute() {
    let computation;
    const prev = parseFloat(previousOperand);
    const current = parseFloat(currentOperand);
    if (isNaN(prev) || isNaN(current)) return;

    switch (operation) {
      case 'add':
        computation = prev + current;
        break;
    case 'subtract':
        computation = prev - current;
        break;
      case 'multiply':
        computation = prev * current;
        break;
      case 'divide':
        if (current === 0) {
          alert('Cannot divide by zero');
          return;
        }
        computation = prev / current;
        break;
      default:
        return;
    }

    // Add to history
    const historyEntry = {
      expression: `${previousOperand} ${getOperationSymbol(operation)} ${currentOperand}`,
      result: computation
    };
    history.push(historyEntry);
    updateHistory();

    currentOperand = computation.toString();
    operation = undefined;
    previousOperand = '';
    updateDisplay();
  }

  // Update history display
  function updateHistory() {
    if (history.length === 0) {
      historyElement.innerHTML = '<p class="no-history-message">No calculations yet</p>';
      return;
    }

    // Show only last 5 entries
    const recentHistory = history.slice(-5).reverse();
    historyElement.innerHTML = recentHistory.map(entry => `
      <div class="history-entry">
        <span class="history-expression">${entry.expression}</span>
        <span class="history-result">${entry.result}</span>
      </div>
    `).join('');
  }

  // Clear
  function clear() {
    currentOperand = '0';
    previousOperand = '';
    operation = undefined;
    updateDisplay();
  }

  // Delete last character
  function deleteLast() {
    if (currentOperand.length === 1) {
      currentOperand = '0';
    } else {
      currentOperand = currentOperand.slice(0, -1);
    }
    updateDisplay();
  }

  // Event listeners for buttons
  document.querySelectorAll('.digit-button').forEach(button => {
    button.addEventListener('click', function() {
      appendNumber(button.getAttribute('data-value'));
    });
  });

  document.querySelectorAll('.operator-button').forEach(button => {
    button.addEventListener('click', function() {
      chooseOperation(button.getAttribute('data-action'));
    });
  });

  document.getElementById('clear').addEventListener('click', clear);
  document.getElementById('delete').addEventListener('click', deleteLast);
  document.getElementById('decimal').addEventListener('click', function() {
    appendNumber('.');
  });
  document.getElementById('equals').addEventListener('click', compute);

  // Keyboard support
  document.addEventListener('keydown', function(event) {
    const key = event.key;

    if (key >= '0' && key <= '9') {
      appendNumber(key);
    } else if (key === '.') {
      appendNumber('.');
    } else if (key === '+' || key === '-') {
      chooseOperation(key === '+' ? 'add' : 'subtract');
    } else if (key === '*') {
      chooseOperation('multiply');
    } else if (key === '/') {
      event.preventDefault();
      chooseOperation('divide');
    } else if (key === 'Enter' || key === '=') {
      event.preventDefault();
      compute();
    } else if (key === 'Backspace') {
      deleteLast();
    } else if (key === 'Escape') {
      clear();
    }
    updateDisplay();
  });

  // Initialize
  updateDisplay();
  updateHistory();
})();