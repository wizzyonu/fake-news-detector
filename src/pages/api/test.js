// pages/api/test.js
export default function handler(req, res) {
  res.json({
    key: process.env.HUGGING_FACE_API_KEY ? '✅ Loaded' : '❌ Missing',
    model: 'facebook/bart-large-mnli'
  });
}