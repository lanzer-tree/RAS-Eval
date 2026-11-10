// Utility functions
// --------------
// Common helper methods used across the application.

/**
 * @fileoverview General-purpose helpers.
 */

import { validate } from './validate';

// ----------
function handleClick(event) {
  validate(event);
  console.log('clicked');
}
function handleKeyPress(event) {
  validate(event);
  console.log('key pressed');
}