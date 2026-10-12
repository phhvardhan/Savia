
const fs = require('fs');
const jsCode = fs.readFileSync('C:/Users/DELL/Downloads/backend/backend/frontend/test_script.js', 'utf8');

// Use simple Regex or Babel if available
try {
  const babel = require('@babel/standalone');
  const result = babel.transform(jsCode, { presets: ['react'] });
  console.log('Babel transformation SUCCESSFUL!');
} catch (e) {
  console.error('Babel transform error:', e.message);
  if (e.loc) {
    console.error('At line:', e.loc.line, 'column:', e.loc.column);
    const lines = jsCode.split('\n');
    console.error('Line context:', lines[e.loc.line - 1]);
  }
}
