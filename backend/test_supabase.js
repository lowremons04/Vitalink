// FILE: backend/test_supabase.js
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

console.log('Attempting to connect to Supabase...');
console.log('URL:', supabaseUrl);

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  console.log('\nAttempting to insert a test row...');
  const { data, error } = await supabase
    .from('readings')
    .insert([{ sys: 1, dia: 1, pulse: 1 }]);

  if (error) {
    console.error('\n--- TEST FAILED ---');
    console.error('Supabase returned an error:', error);
  } else {
    console.log('\n--- TEST SUCCEEDED ---');
    console.log('Successfully inserted data:', data);
  }
}

testConnection();