// test-dataset.js
const dataset = require('./data/datasets.json');

async function testSample(sample) {
  try {
    const response = await fetch('http://localhost:3000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: sample.text })
    });
    
    const result = await response.json();
    
    // ✅ FIX: Use 'label' field to match dataset.json
    const expectedLabel = sample.label || sample.expected || 'UNKNOWN';
    const actualLabel = result.classification;
    const match = expectedLabel === actualLabel;
    
    console.log(`ID ${sample.id}: Expected=${expectedLabel}, Actual=${actualLabel}, Confidence=${result.confidence}%, Match=${match ? '✅' : '❌'}`);
    
    return {
      ...sample,
      actual: actualLabel,
      confidence: result.confidence,
      match: match
    };
  } catch (error) {
    console.error(`ID ${sample.id}: Error - ${error.message}`);
    return {
      ...sample,
      actual: 'ERROR',
      confidence: 0,
      match: false
    };
  }
}

// Run all tests
async function runTests() {
  console.log(`\n🧪 Starting tests for ${dataset.length} samples...\n`);
  
  const results = [];
  
  for (const sample of dataset) {
    const result = await testSample(sample);
    results.push(result);
    
    // Add delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Calculate statistics
  const totalTests = results.length;
  const correctTests = results.filter(r => r.match).length;
  const accuracy = totalTests > 0 ? (correctTests / totalTests) * 100 : 0;
  
  // ✅ FIX: Filter using the correct field name
  const realSamples = results.filter(r => r.label === 'REAL' || r.expected === 'REAL');
  const fakeSamples = results.filter(r => r.label === 'FAKE' || r.expected === 'FAKE');
  
  const realAccuracy = realSamples.length > 0 ? (realSamples.filter(r => r.match).length / realSamples.length) * 100 : 0;
  const fakeAccuracy = fakeSamples.length > 0 ? (fakeSamples.filter(r => r.match).length / fakeSamples.length) * 100 : 0;
  
  const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / totalTests;
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Samples Tested:    ${totalTests}`);
  console.log(`Correct Classifications: ${correctTests}`);
  console.log(`Incorrect Classifications: ${totalTests - correctTests}`);
  console.log(`Overall Accuracy:        ${accuracy.toFixed(2)}%`);
  console.log('─'.repeat(60));
  console.log(`REAL Samples Accuracy:   ${realAccuracy.toFixed(2)}% (${realSamples.filter(r => r.match).length}/${realSamples.length})`);
  console.log(`FAKE Samples Accuracy:   ${fakeAccuracy.toFixed(2)}% (${fakeSamples.filter(r => r.match).length}/${fakeSamples.length})`);
  console.log('─'.repeat(60));
  console.log(`Average Confidence:      ${avgConfidence.toFixed(2)}%`);
  console.log(`Min Confidence:          ${Math.min(...results.map(r => r.confidence))}%`);
  console.log(`Max Confidence:          ${Math.max(...results.map(r => r.confidence))}%`);
  console.log('='.repeat(60));
  
  // Save results to file
  const fs = require('fs');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `test-results-${timestamp}.json`;
  
  fs.writeFileSync(filename, JSON.stringify(results, null, 2));
  console.log(`\n💾 Detailed results saved to: ${filename}`);
  
  // Show misclassified samples
  const misclassified = results.filter(r => !r.match);
  if (misclassified.length > 0) {
    console.log('\n❌ MISCLASSIFIED SAMPLES:');
    console.log('─'.repeat(60));
    misclassified.forEach(sample => {
      const expectedLabel = sample.label || sample.expected || 'UNKNOWN';
      console.log(`ID ${sample.id}: "${sample.text.substring(0, 60)}..."`);
      console.log(`   Expected: ${expectedLabel}, Got: ${sample.actual} (${sample.confidence}%)\n`);
    });
  }
}

// Run the tests
runTests().catch(console.error);