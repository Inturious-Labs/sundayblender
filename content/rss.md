---
title: "Subscribe with RSS"
draft: false
disableReadingTime: true
disableToC: true
disableSubscribe: true
disablePagination: true
build:
  list: false
  render: true
---

## RSS Feed URL

Subscribe to The Sunday Blender using your favorite RSS reader!

<div class="rss-url-container" style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
  <input type="text" id="rssUrl" value="https://weekly.sundayblender.com/index.xml" readonly style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; background: white;">
  <button onclick="copyRssUrl()" style="margin-top: 10px; padding: 8px 16px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer;">
    Copy URL
  </button>
</div>

## How to Use

1. **Copy the RSS feed URL** above
2. **Paste it into your RSS reader** (Feedly, Feeder, etc.)
3. **Stay updated** with our latest posts!

## Popular RSS Readers

- [Feedly](https://feedly.com/) - Web and mobile
- [Feeder](https://feeder.co/) - Browser extension
- [Inoreader](https://www.inoreader.com/) - Web-based
- [NetNewsWire](https://netnewswire.com/) - Mac and iOS

<script>
function copyRssUrl() {
  const rssUrl = document.getElementById('rssUrl');
  rssUrl.select();
  rssUrl.setSelectionRange(0, 99999); // For mobile devices
  
  try {
    document.execCommand('copy');
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.style.background = '#28a745';
    
    setTimeout(() => {
      button.textContent = originalText;
      button.style.background = '#007cba';
    }, 2000);
  } catch (err) {
    console.log('Copy failed');
  }
}
</script>
