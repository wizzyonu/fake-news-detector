// test-coaid.js
const coaidDataset = require('./data/coaid-sample.json');

async function testSample(sample) {
  try {
    const response = await fetch('http://localhost:3000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: sample.text })
    });
    
    const result = await response.json();
    
    const expectedLabel = sample.expected;
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

async function runCoaidTests() {
  console.log(`\n🧪 Starting CoAID tests for ${coaidDataset.length} samples...\n`);
  
  const results = [];
  
  for (const sample of coaidDataset) {
    const result = await testSample(sample);
    results.push(result);
    
    // Add delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Calculate statistics
  const totalTests = results.length;
  const correctTests = results.filter(r => r.match).length;
  const accuracy = totalTests > 0 ? (correctTests / totalTests) * 100 : 0;
  
  const fakeSamples = results.filter(r => r.expected === 'FAKE');
  const realSamples = results.filter(r => r.expected === 'REAL');
  
  const fakeAccuracy = fakeSamples.length > 0 ? (fakeSamples.filter(r => r.match).length / fakeSamples.length) * 100 : 0;
  const realAccuracy = realSamples.length > 0 ? (realSamples.filter(r => r.match).length / realSamples.length) * 100 : 0;
  
  const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / totalTests;
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 CoAID TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Samples Tested:    ${totalTests}`);
  console.log(`Correct Classifications: ${correctTests}`);
  console.log(`Incorrect Classifications: ${totalTests - correctTests}`);
  console.log(`Overall Accuracy:        ${accuracy.toFixed(2)}%`);
  console.log('─'.repeat(60));
  console.log(`FAKE Samples Accuracy:   ${fakeAccuracy.toFixed(2)}% (${fakeSamples.filter(r => r.match).length}/${fakeSamples.length})`);
  console.log(`REAL Samples Accuracy:   ${realAccuracy.toFixed(2)}% (${realSamples.filter(r => r.match).length}/${realSamples.length})`);
  console.log('─'.repeat(60));
  console.log(`Average Confidence:      ${avgConfidence.toFixed(2)}%`);
  console.log(`Min Confidence:          ${Math.min(...results.map(r => r.confidence))}%`);
  console.log(`Max Confidence:          ${Math.max(...results.map(r => r.confidence))}%`);
  console.log('='.repeat(60));
  
  // Save results
  const fs = require('fs');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `coaid-results-${timestamp}.json`;
  
  fs.writeFileSync(filename, JSON.stringify(results, null, 2));
  console.log(`\n💾 CoAID results saved to: ${filename}`);
  
  // Show misclassified
  const misclassified = results.filter(r => !r.match);
  if (misclassified.length > 0) {
    console.log('\n❌ MISCLASSIFIED CoAID SAMPLES:');
    console.log('─'.repeat(60));
    misclassified.forEach(sample => {
      console.log(`ID ${sample.id}: "${sample.text.substring(0, 60)}..."`);
      console.log(`   Expected: ${sample.expected}, Got: ${sample.actual} (${sample.confidence}%)\n`);
    });
  }
  
  return { accuracy, fakeAccuracy, realAccuracy, avgConfidence };
}

// Run tests
runCoaidTests().then(stats => {
  console.log('\n✅ CoAID testing complete. Use these metrics in Chapter 4:');
  console.log(`- Accuracy: ${stats.accuracy.toFixed(1)}%`);
  console.log(`- FAKE Recall: ${stats.fakeAccuracy.toFixed(1)}%`);
  console.log(`- REAL Precision: ${stats.realAccuracy.toFixed(1)}%`);
}).catch(console.error);