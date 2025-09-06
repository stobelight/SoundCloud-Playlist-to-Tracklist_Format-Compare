let formattedOutput = [];
let csvRows = [];

function processTracklist() {
  const rawInput = document.getElementById('trackInput').value;
  const lines = rawInput.split('\n').map(line => line.trim()).filter(Boolean);

  // Config inputs
  const sortOption = document.getElementById('sortOption').value;
  const prefix = parseInt(document.getElementById('prefix').value);
  const maxLength = parseInt(document.getElementById('maxLength').value);
  const removePrefixOption = document.getElementById('removePrefix').checked;
  const replaceSeparator = document.getElementById('replaceSeparator').checked;
  const replaceWith = document.getElementById('replaceWith').value;
  const separators = document.getElementById('separators').value.split(',').map(s => s.trim()).filter(Boolean);
  const blocklist = document.getElementById('blocklist').value.split(',').map(s => s.trim().toLowerCase());

  formattedOutput = [];
  csvRows = [];
  let i = 0;

  while (i < lines.length) {
    const numberLine = lines[i];
    const trackLine = lines[i + 1] || '';
    const popularityLine = lines[i + 2] || '';
    const numberMatch = numberLine.match(/^(\d+)/);

    if (!numberMatch) {
      i++;
      continue;
    }

    const trackNumber = parseInt(numberMatch[1]) + prefix;
    let artist = '', title = '';

    for (const sep of separators) {
      if (trackLine.includes(sep)) {
        [artist, title] = trackLine.split(sep).map(s => s.trim());
        break;
      }
    }

    if (!title) {
      artist = trackLine.trim();
    }

    if (blocklist.includes(artist.toLowerCase())) {
      artist = '';
      title = trackLine;
    }

    let finalLine = replaceSeparator && title ? `${artist}${replaceWith}${title}` : trackLine;
    finalLine = finalLine.slice(0, maxLength);

    formattedOutput.push(`${trackNumber}. ${finalLine}`);
    csvRows.push({ number: trackNumber, artist, title, popularity: popularityLine });

    searchYouTube(`${artist} ${title}`, trackNumber);
    i += popularityLine.match(/^\d+(\.\d+)?[KMBkmb]?$/) ? 3 : 2;
  }

  if (sortOption === 'track') {
    formattedOutput.sort((a, b) => a.split('. ')[1].localeCompare(b.split('. ')[1]));
  } else if (sortOption === 'number') {
    formattedOutput.sort((a, b) => parseInt(a) - parseInt(b));
  }

  if (removePrefixOption) {
    formattedOutput = formattedOutput.map(line => line.replace(/^\d+\.\s*/, ''));
  }

  document.getElementById('output').textContent = formattedOutput.join('\n');
}

// 🔍 YouTube Search (requires API key)
const YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'; // Replace with your actual key

function searchYouTube(query, trackNumber) {
  fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(query)}&maxResults=1&type=video&key=${YOUTUBE_API_KEY}`)
    .then(res => res.json())
    .then(data => {
      if (data.items && data.items.length > 0) {
        const video = data.items[0];
        const videoId = video.id.videoId;
        const title = video.snippet.title;
        const link = `https://www.youtube.com/watch?v=${videoId}`;
        const resultHTML = `<p><strong>${trackNumber}</strong>: <a href="${link}" target="_blank">${title}</a></p>`;
        document.getElementById('youtubeResults').innerHTML += resultHTML;
      }
    })
    .catch(err => console.error('YouTube search error:', err));
}

// 📤 CSV Export
function exportCSV() {
  const headers = ['Track Number', 'Artist', 'Title', 'Plays'];
  const rows = csvRows.map(row => [row.number, row.artist, row.title, row.popularity]);

  let csvContent = 'data:text/csv;charset=utf-8,' + headers.join(',') + '\n';
  csvContent += rows.map(e => e.map(v => `"${v}"`).join(',')).join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', 'tracklist.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
